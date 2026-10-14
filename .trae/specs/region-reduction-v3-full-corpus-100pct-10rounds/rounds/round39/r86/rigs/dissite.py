"""Disassemble one code object of a pyc with source-line mapping (co_lines), offset windowed.

usage: python -X utf8 work/dissite.py <abs pyc> <co-substring> [start_offset] [end_offset]
"""
import dis
import marshal
import os
import sys
import types

REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"

pyc = sys.argv[1]
needle = sys.argv[2]
lo = int(sys.argv[3]) if len(sys.argv) > 3 else 0
hi = int(sys.argv[4]) if len(sys.argv) > 4 else 10 ** 9


def walk(c):
    yield c
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            yield from walk(k)


with open(pyc, 'rb') as fh:
    fh.read(16)
    code = marshal.load(fh)

for co in walk(code):
    names = getattr(co, 'co_qualname', None) or co.co_name
    if needle.lower() not in names.lower():
        continue
    linemap = {}
    try:
        for start, end, line in co.co_lines():
            linemap[start] = line
    except Exception:
        pass
    offs = sorted(linemap)
    print('==== %s  argcount=%s  firstlineno=%s' % (names, co.co_argcount, co.co_firstlineno))
    last = None
    for i in dis.get_instructions(co):
        ln = None
        for o in offs:
            if o <= i.offset:
                ln = linemap[o]
        if i.offset < lo or i.offset > hi:
            continue
        if ln != last:
            print('  --- line %s' % ln)
            last = ln
        if i.opname in ('NOP', 'CACHE', 'EXTENDED_ARG'):
            continue
        print('@%-6s %-34s %s' % (i.offset, i.opname, i.argrepr or ''))
