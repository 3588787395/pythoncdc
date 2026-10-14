"""Round-2 diagnostic helper (test-side, read-only; judge remains scripts/pyc_verify.py).

Usage:
  python -X utf8 test_repros/round2/_r2diag.py diff <orig.pyc> <prod.py|prod.pyc> <name>
      -> instruction alignment where every JUMP/FOR_ITER operand is replaced by a
         CONTENT LABEL of its destination block (first <=4 opnames after it, CACHE
         skipped).  Pure re-alignment (target offset shifted but destination same)
         therefore compares EQUAL, so anything printed is a genuine edge/member diff.
         EXTENDED_ARG / NOP insert-delete rows are tagged [artifact?].
  python -X utf8 test_repros/round2/_r2diag.py blocks <pyc|py> <name>
      -> basic blocks: start offset, lineno, last opcode, successors (fall/jump/handler)
  python -X utf8 test_repros/round2/_r2diag.py tree <pyc|py>
"""
import dis
import marshal
import sys
import types

JUMP_PREFIX = ('JUMP_', 'POP_JUMP_', 'FOR_ITER', 'SEND', 'ASYNC_')
ARTIFACT_OPS = {'EXTENDED_ARG', 'NOP', 'CACHE', 'RESUME'}


def _load(path):
    if path.endswith('.pyc'):
        with open(path, 'rb') as f:
            return marshal.loads(f.read()[16:])
    with open(path, encoding='utf-8') as f:
        return compile(f.read(), path, 'exec')


def walk(code, prefix=''):
    out = []
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            n = f'{prefix}{c.co_name}'
            out.append((n, c))
            out.extend(walk(c, n + '.'))
    return out


def find(code, name):
    for n, c in walk(code):
        if n == name or n.endswith('.' + name) or c.co_name == name:
            return c
    return None


def insns(code):
    return [i for i in dis.get_instructions(code) if i.opname != 'CACHE']


def label(code, tag):
    """(opname, operand-label, offset, lineno) with jumps labelled by destination content."""
    seq = insns(code)
    by_off = {i.offset: k for k, i in enumerate(seq)}

    def dest(off):
        k = by_off.get(off)
        if k is None:
            return f'x{off}'
        return ','.join(x.opname for x in seq[k:k + 4])

    out = []
    for i in seq:
        if i.opname.startswith(JUMP_PREFIX):
            try:
                t = int(i.argval)
            except (TypeError, ValueError):
                t = None
            op = i.opname + ('<BACK>' if (t is not None and t <= i.offset) else '')
            out.append((op, dest(t) if t is not None else str(i.argval), i.offset, i.starts_line))
        else:
            v = i.argval
            if isinstance(v, types.CodeType):
                v = f'<code {v.co_name}:{len(insns(v))}ins>'
            out.append((i.opname, str(v), i.offset, i.starts_line))
    return out


def cmd_diff(orig, prod, name):
    co = find(_load(orig), name)
    cp = find(_load(prod), name)
    if co is None or cp is None:
        print('MISSING', 'orig' if co is None else 'prod', name)
        return
    a, b = label(co, 'orig'), label(cp, 'prod')
    print(f'### {name}  orig {len(a)} insns | prod {len(b)} insns')
    sm = __import__('difflib').SequenceMatcher(None, [(x[0], x[1]) for x in a],
                                               [(x[0], x[1]) for x in b], autojunk=False)
    tags = sm.get_opcodes()
    real = [t for t in tags if t[0] != 'equal']
    print('   opcodes:', [(t[0], t[1], t[3]) for t in tags][:12], '...' if len(tags) > 12 else '')
    if not real:
        print('   NO divergence at all (identical up to CACHE/line numbers)')
        return
    for kind, i1, i2, j1, j2 in real[:4]:
        _seg = [x[0] for x in a[i1:i2]] + [x[0] for x in b[j1:j2]]
        art = bool(_seg) and all(x in ARTIFACT_OPS for x in _seg)
        print(f'   --- {kind}{" [artifact]" if art else ""} orig[{i1}:{i2}] off'
              f'{a[i1][2] if i1 < len(a) else "-"} vs prod[{j1}:{j2}] off'
              f'{b[j1][2] if j1 < len(b) else "-"} ---')
        lo = max(0, i1 - 6)
        for k in range(lo, min(len(a), i2 + 8)):
            op, av, off, ln = a[k]
            print(f'    {"ORIG" if lo <= k < i2 else "    "}  off{off:5d} ln{ln} {op:<30} {av[:70]}')
        lo = max(0, j1 - 6)
        for k in range(lo, min(len(b), j2 + 8)):
            op, av, off, ln = b[k]
            print(f'    {"PROD" if lo <= k < j2 else "    "}  off{off:5d} ln{ln} {op:<30} {av[:70]}')


def cmd_blocks(path, name, only=None):
    code = find(_load(path), name)
    if code is None:
        print('MISSING', name)
        return
    seq = insns(code)
    offs = [i.offset for i in seq]
    last_off = offs[-1]
    import bisect

    def nx_after(ro, off):
        k = bisect.bisect_right(ro, off)
        return ro[k] if k < len(ro) else None

    roffs = offs
    starts = {offs[0]}
    for i in seq:
        if i.opname.startswith(JUMP_PREFIX):
            try:
                starts.add(int(i.argval))
            except (TypeError, ValueError):
                pass
        if i.opname not in ('RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS', 'RERAISE',
                            'POP_EXCEPTION') and not i.opname.startswith('JUMP_BACKWARD'):
            nxt = nx_after(roffs, i.offset)
            if nxt is not None and nxt <= last_off:
                starts.add(nxt)
    for e in (dis.exceptions(code) if hasattr(dis, 'exceptions') else []):
        starts.add(e.handler)
        starts.add(e.start)
    starts = sorted(s for s in starts if s in offs)
    bid = {s: k for k, s in enumerate(starts)}
    nxt_start = {s: (starts[k + 1] if k + 1 < len(starts) else 1 << 30)
                 for k, s in enumerate(starts)}
    succ, pred = {}, {}
    for k, s in enumerate(starts):
        blk = [i for i in seq if s <= i.offset < nxt_start[s]]
        t = []
        last = blk[-1]
        if last.opname.startswith(JUMP_PREFIX):
            try:
                tj = int(last.argval)
                if tj in bid:
                    t.append(('jump', bid[tj]))
            except (TypeError, ValueError):
                pass
        term = last.opname in ('RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS', 'RERAISE')
        if not term and not last.opname.startswith('JUMP_'):
            nx = nx_after(roffs, last.offset)
            if nx in bid:
                t.append(('fall', bid[nx]))
        if last.opname.startswith('POP_JUMP'):
            nx = nx_after(roffs, last.offset)
            if nx in bid:
                t.append(('fall', bid[nx]))
        for e in (dis.exceptions(code) if hasattr(dis, 'exceptions') else []):
            if e.start <= s < e.end or s == e.start:
                if e.handler in bid:
                    t.append(('hdl', bid[e.handler]))
        succ[k] = (t, last.opname, term)
        for _, d in t:
            pred.setdefault(d, []).append((k, t[-1][0] if t else '?'))
    print(f'=== blocks of {name} from {path.split("/")[-1]} ({len(starts)} blocks) ===')
    for k, s in enumerate(starts):
        blk = [i for i in seq if s <= i.offset < nxt_start[s]]
        head = ','.join(x.opname for x in blk[:4])
        consts = ','.join(str(x.argval) for x in blk if x.opname in
                          ('LOAD_CONST', 'LOAD_GLOBAL', 'LOAD_METHOD', 'LOAD_ATTR', 'STORE_SUBSCR')
                          and not isinstance(x.argval, types.CodeType))[:46]
        tag = succ[k][0]
        pd = sorted({p[0] for p in pred.get(k, [])})
        if only is not None and k != only:
            continue
        print(f'B{k:<3d} off{s:5d} ln{blk[0].starts_line} n={len(blk):3d} last={succ[k][1]:<26} '
              f'succ={[f"{w}:{d}" for w, d in tag]} preds={pd} | {head} | {consts}')


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'diff':
        cmd_diff(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == 'blocks':
        cmd_blocks(sys.argv[2], sys.argv[3])
    elif cmd == 'tree':
        for n, c in walk(_load(sys.argv[2])):
            print(f'{n}  insns={len(insns(c))}')
