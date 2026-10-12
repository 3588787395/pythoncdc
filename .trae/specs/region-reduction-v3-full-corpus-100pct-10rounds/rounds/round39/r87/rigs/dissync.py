"""Dump one unit's original instructions with resolved jump targets (from dis itself) and source
lines from co_lines. Never hand-resolves a jump: `Instruction.targets` is supplied by dis.

usage: python -X utf8 dissync.py <pyc-abs> <unit-dotted-name> [start_offset] [end_offset]
"""
import dis
import importlib.util
import marshal
import sys

spec = importlib.util.spec_from_file_location('ud', 'unit_diff.py')
ud = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ud)

pyc, name = sys.argv[1], sys.argv[2]
lo = int(sys.argv[3]) if len(sys.argv) > 3 else 0
hi = int(sys.argv[4]) if len(sys.argv) > 4 else 1 << 30

codes = []
ud.gather(marshal.loads(open(pyc, 'rb').read()[16:]), codes)
co = ud.pick(codes, name)

line_of = {}
for (start, end, line) in co.co_lines():
    if line is None:
        continue
    for i in range(start, max(end, start + 2), 2):
        line_of.setdefault(i, line)

idx = {}
n = 0
for i in dis.get_instructions(co):
    idx[i.offset] = n
    n += 1

for i in dis.get_instructions(co):
    if not (lo <= i.offset <= hi):
        continue
    tg = list(getattr(i, 'targets', None) or
              ([i.target] if getattr(i, 'target', None) is not None else []))
    t = ' -> ' + ','.join('@%d#%d' % (g, idx.get(g, -1)) for g in tg) if tg else ''
    print('@%-6d #%-4d L%-5s %-28s %s%s' % (
        i.offset, idx[i.offset], line_of.get(i.offset, ''),
        i.opname, i.argrepr or '', t))
