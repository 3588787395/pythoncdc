# -*- coding: utf-8 -*-
"""diag4 r67: disassemble one function of a decompiled *product* .py (compiled in-memory).
usage: python -X utf8 pdis.py <okpy> <funcname> [--start=N --end=N]
"""
import dis
import io
import sys
import types

sys.stdout.reconfigure(encoding='utf-8')

path, name = sys.argv[1], sys.argv[2]
kw = dict(x[2:].split('=', 1) for x in sys.argv[3:])
lo, hi = int(kw.get('start', 0)), int(kw.get('end', 1 << 30))
src = io.open(path, encoding='utf-8').read()
lines = {n + 1: l for n, l in enumerate(src.splitlines())}
mod = compile(src, path, 'exec')


def walk(c, out):
    out.append(c)
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            walk(k, out)
    return out


cs = [c for c in walk(mod, []) if c.co_name == name]
print('# %d match(es)' % len(cs))
for c in cs:
    print('=== %s firstlineno=%d args=%s ===' % (c.co_name, c.co_firstlineno, c.co_varnames))
    last = None
    for i in dis.get_instructions(c):
        if i.opname == 'CACHE':
            continue
        ln = getattr(i, 'line_number', None) or getattr(i, 'starts_line', None)
        if ln is not None and ln != last:
            last = ln
            print('      -- line %d: %s' % (last, lines.get(last, '').strip()[:110]))
        if lo <= i.offset <= hi:
            print('  %5d %-30s %s' % (i.offset, i.opname, i.argrepr))
