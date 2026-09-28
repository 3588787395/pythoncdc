# -*- coding: utf-8 -*-
"""R75 diag1 · tick75.py — real_quote.get_tick_direction 的 ADR-1 hunk 解剖（只读）。

对每个臂（landed=仓库 OK.py / absj / absj3 / absj9 / absjt / try7_9 / try7_10d）算
adr73 同口径指标，并把 **归一化 SequenceMatcher hunk 的指令级内容** 全文列出，
用于指认 absj9/absjt 上 hunks_norm 2→3 新增的那一处。
输出 dump/tick_direction75.md。
用法：python -X utf8 tick75.py
"""
import io
import dis
import json
import marshal
import os
import re
import sys
import tempfile
import shutil
import types as _t
import warnings
import py_compile
from difflib import SequenceMatcher

warnings.filterwarnings('ignore')
PYLINGUAL = r'D:\Desktop\ptrade相关\pylingual'
sys.path.insert(0, PYLINGUAL)
import typing
if not hasattr(typing, 'override'):
    typing.override = lambda f: f
if 'pydot' not in sys.modules:
    _s = _t.ModuleType('pydot')
    _s.graph_from_dot_data = lambda *a, **k: []
    _s.Dot = _s.Node = _s.Edge = lambda *a, **k: None
    sys.modules['pydot'] = _s
if 'pylingual' not in sys.modules:
    _p = _t.ModuleType('pylingual')
    _p.__path__ = [os.path.join(PYLINGUAL, 'pylingual')]
    sys.modules['pylingual'] = _p

from pylingual.equivalence_check import matching_iter
from pylingual.editable_bytecode import PYCFile
from pylingual.editable_bytecode.bytecode_patches import (
    fix_indirect_jump, fix_unreachable, remove_extended_arg, remove_nop,
    replace_firstlno)

REPO = r'F:/Downloads/pythoncdc-main'
GATE74 = r'D:/Temp/opencode/r74gate/center'
WORK = r'D:/Temp/opencode/r75gate/diag1'
REL = 'IQData/plugins/plugin_system_realquote/real_quote.pyc'
UNIT = '<module>.RealQuoteData.get_tick_direction'
ARMS = ['absj', 'absj3', 'absj9', 'absjt', 'try7_9', 'try7_10d', 'try7_3']
PATCHES = [remove_extended_arg, remove_nop, fix_indirect_jump,
           fix_unreachable, remove_extended_arg, replace_firstlno]
JUMPISH = re.compile(r'^(JUMP|POP_JUMP|FOR_ITER|SEND)')
OUT = os.path.join(WORK, 'dump', 'tick_direction75.md')
sys.stdout.reconfigure(encoding='utf-8')


def load_pyc(path):
    data = io.open(path, 'rb').read()
    for off in (16, 12, 8):
        try:
            return marshal.loads(data[off:])
        except Exception:
            continue
    raise SystemExit('cannot unmarshal ' + path)


def walk(code, prefix, out):
    out[prefix] = code
    for c in code.co_consts:
        if isinstance(c, _t.CodeType):
            walk(c, prefix + '.' + c.co_name, out)
    return out


def find_code(co, target, path='<module>'):
    if path == target:
        return co
    for c in co.co_consts:
        if isinstance(c, _t.CodeType):
            r = find_code(c, target, path + '.' + c.co_name)
            if r is not None:
                return r
    return None


def key_raw(t):
    return t[0] + ((' ' + t[1]) if t[1] else '')


def key_norm(t):
    op, arg, av = t
    if op.startswith(('JUMP', 'POP_JUMP', 'FOR_ITER', 'SEND')) or arg.startswith('to '):
        return op + ' J'
    if '<code object' in arg:
        return op + ' CODEOBJ'
    return op + ((' ' + arg) if arg else '')


def tup(x):
    return (x.opname, x.argrepr if x.arg is not None else '', x.argval)


def seq_of(src, tmp, tag, A):
    rec = os.path.join(tmp, tag + '.pyc')
    py_compile.compile(src, cfile=rec, doraise=True, optimize=0)
    P = PYCFile(rec)
    P.apply_patches(PATCHES)
    ia = ib = None
    for ba, bb in matching_iter(A, P):
        if ba is not None and ba.name == UNIT:
            ia = list(ba)
        if bb is not None and bb.name == UNIT:
            ib = list(bb)
    return ia, ib


def metrics(ia, ib):
    ka, kb = [key_raw(x) for x in ia], [key_raw(x) for x in ib]
    sm = SequenceMatcher(None, ka, kb, autojunk=False)
    hunks = [o for o in sm.get_opcodes() if o[0] != 'equal']
    na, nb = [key_norm(x) for x in ia], [key_norm(x) for x in ib]
    sm2 = SequenceMatcher(None, na, nb, autojunk=False)
    hunks_n = [o for o in sm2.get_opcodes() if o[0] != 'equal']
    first = None
    n = min(len(ia), len(ib))
    for k in range(n):
        if ia[k][0] != ib[k][0] or ia[k][1] != ib[k][1]:
            first = k
            break
    if first is None and len(ia) != len(ib):
        first = n
    sd = 0
    deltas = []
    for k in range(n):
        a, b = ia[k], ib[k]
        if a[0] == b[0] and JUMPISH.match(a[0]) and isinstance(a[2], int) and isinstance(b[2], int) \
                and a[2] != b[2]:
            sd += abs(b[2] - a[2])
            deltas.append([k, a[0], a[1], b[1], b[2] - a[2]])
    # raw ↔ norm hunk 配对：区间相交（orig 侧或 prod 侧）即视为命中
    raw_hit = []
    for t, i1, i2, j1, j2 in hunks:
        if t == 'equal':
            raw_hit.append([])
            continue
        hits = []
        for g, (t2, ai, bi, aj, bj) in enumerate(hunks_n):
            if t2 == 'equal':
                continue
            if (i1 < bi and ai < i2) or (j1 < bj and aj < j2):
                hits.append(g + 1)
        raw_hit.append(hits)
    return dict(hunks=len(hunks), hunks_norm=len(hunks_n), first_diff=first,
                sdelta=sd, deltas=deltas, lens=[len(ia), len(ib)],
                raw_opcodes=hunks, norm_opcodes=hunks_n, ka=ka, kb=kb, na=na, nb=nb,
                ia=ia, ib=ib, raw_hit=raw_hit)


def main():
    out = ['# R75 diag1 · `real_quote.get_tick_direction` ADR-1 解剖（dump/tick_direction75.md）', '',
           '口径与 `center/adr73.py` 完全一致：pylingual `matching_iter` 对齐后按 '
           '`key_raw`（opname+argrepr）/`key_norm`（跳转参数归一为 `J`、code object 归一为 `CODEOBJ`）'
           '做 SequenceMatcher，非 equal 段计 hunk；`sdelta`=|target差| 之和；`deltas` 为跳转 argval 差异。', '',
           '对照臂：`landed` = 仓库 `real_quoteOK.py`；其余 = R74 `center/build_<arm>/` 产物。', '']
    tmp = tempfile.mkdtemp(prefix='tick75_')
    try:
        pyc = os.path.join(REPO, 'site-packages', REL)
        A = PYCFile(pyc)
        A.apply_patches(PATCHES)
        srcs = [('landed', os.path.join(REPO, 'site-packages', REL[:-4] + 'OK.py'))]
        for arm in ARMS:
            p = os.path.join(GATE74, 'build_' + arm,
                             REL.replace('/', '__')[:-4] + 'OK.py')
            if os.path.isfile(p):
                srcs.append((arm, p))
            else:
                out.append('- MISSING build for arm %s: %s' % (arm, p))
        res = {}
        for tag, src in srcs:
            try:
                ia, ib = seq_of(src, tmp, tag, A)
                if ia is None or ib is None:
                    out.append('- %s: UNPAIRED orig=%s prod=%s' % (tag, ia is not None, ib is not None))
                    continue
                res[tag] = metrics([tup(x) for x in ia], [tup(x) for x in ib])
                res[tag]['ins_a'], res[tag]['ins_b'] = ia, ib
            except Exception as ex:
                out.append('- %s: ERR %r' % (tag, ex))
        olen = res.get('landed', {}).get('lens', ['?'])[0]
        out.insert(3, '')
        out.insert(3, '对照单元 `%s`，orig_len=%s。' % (UNIT, olen))
        out.append('## 1. 指标一览（orig_len=%s，取 matched orig）' % olen)
        out.append('')
        out.append('| arm | len[orig,prod] | hunks | hunks_norm | first_diff | sdelta | deltas |')
        out.append('|---|---|---|---|---|---|---|')
        for tag, _ in srcs:
            r = res.get(tag)
            if not r:
                continue
            out.append('| %s | %s | %d | %d | %s | %d | %s |' % (
                tag, r['lens'], r['hunks'], r['hunks_norm'], r['first_diff'], r['sdelta'],
                '; '.join('#%d %s %s->%s (%+d)' % tuple(d) for d in r['deltas'])))
        out.append('')
        out.append('## 2. 归一化 hunk 内容（key_norm 序列上的非 equal 段）')
        out.append('')
        for tag, _ in srcs:
            r = res.get(tag)
            if not r:
                continue
            out.append('### arm=%s · hunks_norm=%d' % (tag, r['hunks_norm']))
            for j, (t, i1, i2, j1, j2) in enumerate(r['norm_opcodes'], 1):
                out.append('- **#%d** `%s` orig[%d:%d] -> prod[%d:%d]' % (j, t, i1, i2, j1, j2))
                if t in ('replace', 'delete'):
                    for k in range(i1, i2):
                        out.append('    - O %4d %-44s  norm=%s' % (k, r['ka'][k], r['na'][k]))
                if t in ('replace', 'insert'):
                    for k in range(j1, j2):
                        out.append('    - P %4d %-44s  norm=%s' % (k, r['kb'][k], r['nb'][k]))
            out.append('')
        out.append('## 3. 原始 hunk（key_raw，含跳转目标数值）')
        out.append('')
        for tag, _ in srcs:
            r = res.get(tag)
            if not r:
                continue
            out.append('### arm=%s · hunks=%d' % (tag, r['hunks']))
            for j, (t, i1, i2, j1, j2) in enumerate(r['raw_opcodes'], 1):
                hits = r['raw_hit'][j - 1]
                ds = [d for d in r['deltas'] if i1 <= d[0] < i2]
                out.append('- **#%d** `%s` orig[%d:%d] -> prod[%d:%d]%s%s' % (
                    j, t, i1, i2, j1, j2,
                    (' · 对应 norm hunk %s' % hits) if hits else ' · norm hunk 无对应',
                    (' · jump-delta %s' % '; '.join('#%d %s %s->%s (%+d)' % tuple(d) for d in ds)) if ds else ''))
                if t in ('replace', 'delete'):
                    for k in range(i1, i2):
                        out.append('    - O %4d %s' % (k, r['ka'][k]))
                if t in ('replace', 'insert'):
                    for k in range(j1, j2):
                        out.append('    - P %4d %s' % (k, r['kb'][k]))
            out.append('')
        # ---- 4. 字节级内容（matched Inst 的 offset / bytecode 切片） ----
        out.append('## 4. 字节级内容（matched 指令表：`idx` / `offset` / `co_code` 字节；'
                   '与 §2、§3 的 index 完全同一空间）')
        out.append('')

        def ibytes(insts, i1, i2):
            rows = []
            for k in range(i1, i2):
                x = insts[k]
                buf = x.bytecode
                try:
                    n = getattr(x, 'inst_size', 2) or 2
                    hx = bytes(buf[x.offset:x.offset + n]).hex()
                except Exception:
                    hx = ''
                ar = x.argrepr if x.arg is not None else ''
                rows.append('- %4d off=%-6d %-6s %-44s %s' % (k, x.offset, hx, x.opname, ar))
            return rows

        la = res.get('landed')
        if la:
            out.append('### orig（matched，len=%d）· 三个归一化 hunk 的 orig 侧' % len(la['ins_a']))
            for j, (tt, i1, i2, j1, j2) in enumerate(la['norm_opcodes'], 1):
                out.append('- hunk #%d `%s` orig[%d:%d]' % (j, tt, i1, i2))
                if i1 < i2:
                    out.extend(ibytes(la['ins_a'], i1, i2))
            out.append('')
        for tag, _ in srcs:
            r = res.get(tag)
            if not r:
                continue
            out.append('### arm=%s（matched，len=%d）· hunks_norm=%d' % (tag, len(r['ins_b']), r['hunks_norm']))
            for j, (tt, i1, i2, j1, j2) in enumerate(r['norm_opcodes'], 1):
                out.append('- hunk #%d `%s` -> prod[%d:%d]' % (j, tt, j1, j2))
                if j1 < j2:
                    out.extend(ibytes(r['ins_b'], j1, j2))
            out.append('')
        io.open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
        print('wrote', OUT)
        for tag, _ in srcs:
            r = res.get(tag)
            if r:
                print('%-9s len=%s hunks=%d norm=%d first=%s sd=%d' %
                      (tag, r['lens'], r['hunks'], r['hunks_norm'], r['first_diff'], r['sdelta']))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
