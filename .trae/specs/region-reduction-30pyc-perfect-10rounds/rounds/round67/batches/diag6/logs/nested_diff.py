# -*- coding: utf-8 -*-
"""Exact per-code-object comparison of a pyc against its decompiled product.
Walks both trees in (co_name, index-in-parent) order and diffs normalized instruction lists.
usage: nested_diff.py <pyc> <okpy> [name-filter]"""
import dis, io, marshal, sys, types
from difflib import SequenceMatcher
sys.stdout.reconfigure(encoding='utf-8')
JUMPS = ('JUMP', 'BRANCH', 'RETURN_GENERATOR')

def norm(op, arg):
    if op.startswith(JUMPS) or arg.startswith('to ') or 'group' in arg: return op + ' J'
    if '<code object' in arg: return op + ' CODEOBJ'
    return op + ' ' + arg

def tree(code, path='', out=None):
    out = [] if out is None else out
    out.append((path or '<root>', code))
    for i, k in enumerate(code.co_consts):
        if isinstance(k, types.CodeType):
            tree(k, '%s/%s#%d' % (path, k.co_name, i), out)
    return out

def instrs(code):
    return [norm(i.opname, str(i.argrepr)) for i in dis.get_instructions(code) if i.opname != 'CACHE']

def load_pyc(p):
    d = io.open(p, 'rb').read()
    for off in (16, 12, 8):
        try: return marshal.loads(d[off:])
        except Exception: pass
    raise SystemExit('bad pyc')

pyc, ok = sys.argv[1], sys.argv[2]
filt = sys.argv[3] if len(sys.argv) > 3 else None
A = tree(load_pyc(pyc))
B = tree(compile(io.open(ok, encoding='utf-8').read(), ok, 'exec'))
bm = {}
for p, c in B: bm.setdefault(p, []).append(c)
bad = 0
for p, c in A:
    if filt and filt not in p: continue
    lst = bm.get(p, [])
    d = lst[0] if lst else None
    if d is None:
        print('MISSING-IN-PRODUCT %s' % p); bad += 1; continue
    ia, ib = instrs(c), instrs(d)
    if ia == ib: continue
    bad += 1
    sm = SequenceMatcher(None, ia, ib, autojunk=False)
    ops = [o for o in sm.get_opcodes() if o[0] != 'equal']
    print('DIFF %-46s orig=%d decomp=%d hunks=%d' % (p, len(ia), len(ib), len(ops)))
    for tag, i1, i2, j1, j2 in ops:
        print('   %-8s orig[%d:%d]=%s  decomp[%d:%d]=%s' % (tag, i1, i2, ia[i1:i2][:6], j1, j2, ib[j1:j2][:6]))
print('TOTAL differing code objects: %d of %d' % (bad, len(A)))
