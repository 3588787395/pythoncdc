#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r4v3 诊断器（只读；不改判据 core/**、scripts/pyc_verify.py）。

用法：
  python -X utf8 _r4v3_diag.py diff   <x.pyc> <xOK.py> [qualname子串]
  python -X utf8 _r4v3_diag.py blocks <x.pyc|xOK.py> [qualname子串]
  python -X utf8 _r4v3_diag.py oseq   <x.pyc> <xOK.py> [qualname子串]

噪声口径（rules.md §5.2/§5.3）：CACHE / EXTENDED_ARG / PRECALL 不入指令序列；
NOP 保留并标注行追踪伪影候选；跳转 argval = 绝对字节偏移，故 argval 差异按
「目标内容签名」判定（同签名 = 位移伪影，可豁免；异签名 = 真边差）。
"""
import sys
import os
import marshal
import dis
import difflib

SKIP = {'CACHE', 'EXTENDED_ARG', 'PRECALL'}
TERM = ('RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS', 'RERAISE')


def load_pyc(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def load_src(path):
    with open(path, encoding='utf-8-sig') as f:
        text = f.read()
    return compile(text, os.path.basename(path), 'exec', dont_inherit=True)


def walk(code, prefix=''):
    yield prefix or '<module>', code
    for c in code.co_consts:
        if hasattr(c, 'co_code'):
            yield from walk(c, (prefix + '.' if prefix else '') + c.co_name)


def live(code):
    return [(i.offset, i.opname, i.argval) for i in dis.get_instructions(code)
            if i.opname not in SKIP]


def sig(ins, off, n=4):
    """从 >= off 的首条 live 指令起的前 n 个 opcode（目标内容签名）。"""
    lo, hi = 0, len(ins)
    while lo < hi:
        mid = (lo + hi) // 2
        if ins[mid][0] < off:
            lo = mid + 1
        else:
            hi = mid
    if lo >= len(ins):
        return '<past-end>'
    return ','.join(x[1] for x in ins[lo:lo + n])


def blocks_of(code):
    ins = live(code)
    if not ins:
        return [], ins
    offs = [i[0] for i in ins]
    oid = {o: k for k, o in enumerate(offs)}

    def snap(o):
        lo, hi = 0, len(offs)
        while lo < hi:
            mid = (lo + hi) // 2
            if offs[mid] < o:
                lo = mid + 1
            else:
                hi = mid
        return offs[lo] if lo < len(offs) else None

    leaders = {offs[0]}
    for k, (o, op, av) in enumerate(ins):
        nxt = offs[k + 1] if k + 1 < len(ins) else None
        sav = snap(av) if isinstance(av, int) else None
        if op.startswith('POP_JUMP') or op == 'FOR_ITER' or op == 'SEND':
            if sav is not None:
                leaders.add(sav)
            if nxt is not None:
                leaders.add(nxt)
        elif op.startswith('JUMP'):
            if sav is not None:
                leaders.add(sav)
        elif op in TERM or op == 'YIELD_VALUE' or op == 'END_ASYNC_FOR':
            if nxt is not None:
                leaders.add(nxt)
    leaders = sorted(o for o in leaders if o in oid)
    bid = {o: n for n, o in enumerate(leaders)}
    blks = [{'id': n, 'start': o, 'instrs': []} for n, o in enumerate(leaders)]
    cur = 0
    for k, it in enumerate(ins):
        if it[0] in bid:
            cur = bid[it[0]]
        blks[cur]['instrs'].append(it)
        tail_off = it[0]
        nxt = offs[k + 1] if k + 1 < len(ins) else None
        op, av = it[1], it[2]
        is_tail = (k == len(ins) - 1) or (blks[cur]['instrs'][-1] is it and k + 1 < len(ins)
                                         and offs[k + 1] in bid)
        if is_tail:
            sav = snap(av) if op.startswith(('JUMP', 'POP_JUMP')) or op in ('FOR_ITER', 'SEND') else None
            if op.startswith('POP_JUMP') or op == 'FOR_ITER' or op == 'SEND':
                blks[cur]['jump'] = bid.get(sav)
                blks[cur]['jump_off'] = sav
                blks[cur]['fall'] = bid.get(nxt)
            elif op.startswith('JUMP'):
                blks[cur]['jump'] = bid.get(sav)
                blks[cur]['jump_off'] = sav
                blks[cur]['fall'] = None
            elif op in TERM:
                blks[cur]['jump'] = blks[cur]['fall'] = None
            else:
                blks[cur]['jump'] = None
                blks[cur]['fall'] = bid.get(nxt)
    for b in blks:
        b.setdefault('jump', None)
        b.setdefault('fall', None)
        b.setdefault('jump_off', None)
    preds = {b['id']: [] for b in blks}
    for b in blks:
        for s in (b['jump'], b['fall']):
            if s is not None:
                preds[s].append(b['id'])
    for b in blks:
        b['preds'] = sorted(set(preds[b['id']]))
    return blks, ins


def do_preds(pyc, src, filt):
    """按块签名跨版本配对，打印 preds 计数发生变化的块（边塌陷/边新增证据）。"""
    co = load_pyc(pyc)
    cj = load_src(src)
    for name, ci, c2 in pair(co, cj):
        if filt and filt not in name:
            continue
        if ci is None or c2 is None:
            continue
        bi, _ = blocks_of(ci)
        bj, _ = blocks_of(c2)
        for x in bi:
            x['fsig'] = ','.join(i[1] for i in x['instrs'])
        for x in bj:
            x['fsig'] = ','.join(i[1] for i in x['instrs'])
        # 只比较块起始 offset 相同的块（重编译后同一位置的块）；offset 位移时用签名兜底
        jb = {b['start']: b for b in bj}
        rows = []
        for b in bi:
            o = jb.get(b['start']) or next((x for x in bj if x['fsig'] == b['fsig']), None)
            if o is None:
                rows.append(('PROD-ONLY-MISSING', b, None))
                continue
            if (b['jump'] is None) != (o['jump'] is None) or b['preds'] != o['preds']:
                rows.append(('PRED/EDGE DIFF', b, o))
        if not rows:
            continue
        print(f'=== {name} orig {len(bi)} blocks / prod {len(bj)} blocks')
        for kind, b, o in rows:
            s = f"off{b['start']} [{b['fsig'][:70]}] jump_off={b.get('jump_off')} preds={b['preds']}"
            if o is None:
                print(f'  [{kind}] ORIG {s}')
            else:
                s2 = f"off{o['start']} jump_off={o.get('jump_off')} preds={o['preds']}"
                print(f'  [{kind}] ORIG {s}  ||  PROD {s2}')


def group(code):
    """按 qualname 分组（同名嵌套 code object 可能有多个，按出现顺序配对）。"""
    out = {}
    for n, c in walk(code):
        out.setdefault(n, []).append(c)
    return out


def pair(co, cj):
    """(label, orig_code, prod_code) —— 同名多个嵌套 code object 按出现顺序配对。"""
    gi, gj = group(co), group(cj)
    for name in gi:
        for k, ci in enumerate(gi[name]):
            lst = gj.get(name, [])
            lbl = name if len(lst) <= 1 else f'{name}#{k}'
            cj2 = lst[k] if k < len(lst) else None
            if cj2 is None:
                yield lbl, ci, None
                continue
            yield lbl, ci, cj2
        if len(gj.get(name, [])) > len(gi[name]):
            for k in range(len(gi[name]), len(gj[name])):
                yield f'{name}#{k}(prod-only)', None, gj[name][k]


def fmt_blk(b, ins):
    ops = ','.join(x[1] for x in b['instrs'])
    js = ''
    if b['jump'] is not None:
        js = f" jump->{b['jump']}(off{b['jump_off']}={sig(ins, b['jump_off'])})"
    fs = ''
    if b['fall'] is not None:
        fs = f" fall->{b['fall']}"
    return f"  B{b['id']:<3} off{b['start']:<5} n={len(b['instrs']):<3} preds={b['preds']}{js}{fs} :: {ops[:130]}"


def do_diff(pyc, src, filt):
    co = load_pyc(pyc)
    cj = load_src(src)
    for name, ci, c2 in pair(co, cj):
        if filt and filt not in name:
            continue
        if c2 is None:
            print(f'[{name}] MISSING in product tree')
            continue
        a, b = live(ci), live(c2)
        idx = None
        for k in range(max(len(a), len(b))):
            ea = a[k] if k < len(a) else None
            eb = b[k] if k < len(b) else None
            if ea != eb:
                idx, iv, jv = k, ea, eb
                break
        if idx is None:
            print(f'[{name}] NO divergence at all (orig {len(a)} / prod {len(b)})')
            continue
        la, lb = len(a), len(b)
        print(f'[{name}] first_diff @{idx} (orig {la} instrs / prod {lb}, delta {lb - la:+d})')
        for k in range(max(0, idx - 4), min(idx + 4, max(la, lb))):
            sa = a[k] if k < la else '-'
            sb = b[k] if k < lb else '-'
            print(f"  {'>>' if k == idx else '  '} o{k}: {sa}   d{k}: {sb}")
        iv_, jv_ = (iv[2] if iv and isinstance(iv[2], int) else None), (jv[2] if jv and isinstance(jv[2], int) else None)
        print('  target-content check:',
              f"ORIG->{sig(a, iv_) if iv_ is not None else '-'}",
              f"| PROD->{sig(b, jv_) if jv_ is not None else '-'}")
        if [x[1] for x in a] == [x[1] for x in b]:
            print('  NOTE opcode sequence identical => only argval(jump target) deltas')


def do_oseq(pyc, src, filt, verbose=False):
    co = load_pyc(pyc)
    cj = load_src(src)
    for name, ci, c2 in pair(co, cj):
        if filt and filt not in name:
            continue
        if ci is None:
            print(f'[{name}] PROD-ONLY code object (orig has none)')
            continue
        if c2 is None:
            print(f'[{name}] MISSING in product tree')
            continue
        a, b = live(ci), live(c2)
        oa, ob = [x[1] for x in a], [x[1] for x in b]
        sm = difflib.SequenceMatcher(None, oa, ob, autojunk=False)
        ops = sm.get_opcodes()
        real = 0
        art = 0
        hdr = f'=== {name}  orig {len(a)} / prod {len(b)} ({len(b) - len(a):+d})'
        lines = []
        for tag, i1, i2, j1, j2 in ops:
            if tag == 'equal':
                # argval deltas inside an equal run
                for k in range(i2 - i1):
                    x, y = a[i1 + k], b[j1 + k]
                    if not x[1].startswith(('JUMP', 'POP_JUMP', 'FOR_ITER', 'SEND')):
                        continue
                    if x[2] != y[2] and isinstance(x[2], int) and isinstance(y[2], int):
                        sa_, sb_ = sig(a, x[2]), sig(b, y[2])
                        if sa_ == sb_:
                            art += 1
                            if verbose:
                                lines.append(f'  [ARTIFACT same-target-content] idx{i1+k} {x[1]} '
                                             f'orig off{x[0]}->{x[2]} prod off{y[0]}->{y[2]} both[{sa_}]')
                            continue
                        real += 1
                        lines.append(f'  [REAL EDGE DELTA] idx{i1+k} {x[1]} orig off{x[0]}->{x[2]}[{sa_}] '
                                     f'prod off{y[0]}->{y[2]}[{sb_}]')
                continue
            real += 1
            lines.append(f'  --- {tag} orig idx[{i1}:{i2}] prod idx[{j1}:{j2}]')
            for k in range(i1, min(i2, i1 + 8)):
                lines.append(f'      O o{k}: {a[k]}  [tgt={sig(a, a[k][2]) if a[k][1].startswith(("JUMP", "POP_JUMP", "FOR_ITER")) else "-"}]')
            for k in range(j1, min(j2, j1 + 8)):
                lines.append(f'      P p{k}: {b[k]}  [tgt={sig(b, b[k][2]) if b[k][1].startswith(("JUMP", "POP_JUMP", "FOR_ITER")) else "-"}]')
        if real or art or lines:
            print(hdr)
            for ln in lines:
                print(ln)
            print(f'  ==> real divergence hunks: {real}  (discounted offset-shift artifacts: {art})')


def do_blocks(path, filt):
    co = load_pyc(path) if path.endswith('.pyc') else load_src(path)
    for name, c in walk(co):
        if filt and filt not in name:
            continue
        blks, ins = blocks_of(c)
        print(f'=== {name}  ({len(ins)} live instrs, {len(blks)} blocks) {os.path.basename(path)}')
        for b in blks:
            print(fmt_blk(b, ins))


if __name__ == '__main__':
    m = sys.argv[1]
    if m == 'blocks':
        do_blocks(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else '')
    else:
        filt = sys.argv[4] if len(sys.argv) > 4 and not sys.argv[4].startswith('-') else ''
        verb = any(a.startswith('-') for a in sys.argv[5:])
        if m == 'diff':
            do_diff(sys.argv[2], sys.argv[3], filt)
        elif m == 'oseq':
            do_oseq(sys.argv[2], sys.argv[3], filt, verb)
        elif m == 'preds':
            do_preds(sys.argv[2], sys.argv[3], filt)
        else:
            print(__doc__)
