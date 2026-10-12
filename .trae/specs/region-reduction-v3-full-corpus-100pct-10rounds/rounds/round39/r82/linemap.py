"""Instruction -> source-line map for either a pyc code object or a compiled product.

usage: python -X utf8 linemap.py <pyc-abs> <unit> [--prod PATH] [--lo N] [--hi N]
"""
import argparse
import dis
import marshal
import sys

ap = argparse.ArgumentParser()
ap.add_argument('pyc')
ap.add_argument('unit')
ap.add_argument('--prod')
ap.add_argument('--lo', type=int, default=0)
ap.add_argument('--hi', type=int, default=10 ** 9)
A = ap.parse_args()


def gather(c, acc):
    acc.append(c)
    for cst in c.co_consts:
        if isinstance(cst, type(c)):
            gather(cst, acc)


def pick(codes, name):
    if '.' in name:
        mods = [c for c in codes if c.co_name == '<module>']
        node = mods[0]
        segs = name.split('.')[1:] if name.startswith('<module>.') else name.split('.')
        for seg in segs:
            nxt = [x for x in node.co_consts if isinstance(x, type(node)) and x.co_name == seg]
            node = nxt[0]
        return node
    for c in codes:
        if c.co_name == name:
            return c
    raise SystemExit('unit not found')


def find_unit(path, name):
    raw = open(path, 'rb').read()
    if path.endswith('.pyc'):
        top = marshal.loads(raw[16:])
    else:
        top = compile(raw.decode('utf-8-sig'), '<p>', 'exec')
    codes = []
    gather(top, codes)
    return pick(codes, name)


def lines_of(co):
    m = {}
    for start, end, line in co.co_lines():
        if line is None:
            continue
        for off in range(start, end, 2):
            m[off] = line
    return m


co = find_unit(A.pyc, A.unit)
if A.prod:
    co = find_unit(A.prod, A.unit)
lm = lines_of(co)
for i in dis.get_instructions(co):
    if not (A.lo <= i.offset <= A.hi):
        continue
    print('@%-6d L%-5s %-30s %s' % (i.offset, lm.get(i.offset, '?'), i.opname, i.argrepr))
