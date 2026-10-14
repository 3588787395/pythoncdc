"""Same as origlist.py but for the PRODUCT source (compile() it, pick the unit).

usage: python -X utf8 prodlist.py <prod.py> <unit> [lo_idx] [hi_idx]
"""
import dis
import importlib.util
import sys

spec = importlib.util.spec_from_file_location('ud', 'unit_diff.py')
ud = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ud)

prod, name = sys.argv[1], sys.argv[2]
lo = int(sys.argv[3]) if len(sys.argv) > 3 else 0
hi = int(sys.argv[4]) if len(sys.argv) > 4 else 1 << 30

comp = compile(open(prod, encoding='utf-8-sig').read(), '<p>', 'exec')
codes = []
ud.gather(comp, codes)
co = ud.pick(codes, name)

line_of = {}
for (start, end, line) in co.co_lines():
    if line is None:
        continue
    for i in range(start, max(end, start + 2), 2):
        line_of.setdefault(i, line)

kept = [i for i in dis.get_instructions(co) if i.opname not in ud.DROP]
off2idx = {i.offset: k for k, i in enumerate(kept)}
for k, i in enumerate(kept):
    if not (lo <= k <= hi):
        continue
    tg = list(getattr(i, 'targets', None) or
              ([i.target] if getattr(i, 'target', None) is not None else []))
    t = '  -> ' + ','.join('@%d#%d' % (g, off2idx.get(g, -1)) for g in tg) if tg else ''
    print('[%-4d] @%-6d L%-5s %-28s %s%s' % (
        k, i.offset, line_of.get(i.offset, ''), i.opname, i.argrepr or '', t))
