"""Filtered instruction list (same DROP as unit_diff.dump) with index, offset, line, opcode, arg,
and jump targets resolved to filtered indices by dis itself.

usage: python -X utf8 origlist.py <pyc-abs> <unit> [lo_idx] [hi_idx]
"""
import dis
import importlib.util
import marshal
import sys

spec = importlib.util.spec_from_file_location('ud', 'unit_diff.py')
ud = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ud)

DROP = ud.DROP
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

kept = [i for i in dis.get_instructions(co) if i.opname not in DROP]
off2idx = {i.offset: k for k, i in enumerate(kept)}
for k, i in enumerate(kept):
    if not (lo <= k <= hi):
        continue
    tg = list(getattr(i, 'targets', None) or
              ([i.target] if getattr(i, 'target', None) is not None else []))
    t = '  -> ' + ','.join('@%d#%d' % (g, off2idx.get(g, -1)) for g in tg) if tg else ''
    print('[%-4d] @%-6d L%-5s %-28s %s%s' % (
        k, i.offset, line_of.get(i.offset, ''), i.opname, i.argrepr or '', t))
