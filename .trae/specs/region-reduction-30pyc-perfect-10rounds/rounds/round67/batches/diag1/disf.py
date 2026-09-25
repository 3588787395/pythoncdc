# -*- coding: utf-8 -*-
"""diag1 dis: full disassembly of one code object (by name) from a .pyc, with LINES marker.

usage: python -X utf8 disf.py <pyc> <funcname> [--src=<okpy to annotate>] [--start=N --end=N]
"""
import dis
import io
import marshal
import sys
import types

sys.stdout.reconfigure(encoding='utf-8')


def load_pyc(path):
    data = io.open(path, 'rb').read()
    for off in (16, 12, 8):
        try:
            return marshal.loads(data[off:])
        except Exception:
            continue
    raise SystemExit('cannot unmarshal %s' % path)


def walk(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, out)
    return out


def find_all(root, name):
    return [c for c in walk(root, []) if c.co_name == name]


if __name__ == '__main__':
    pyc, name = sys.argv[1], sys.argv[2]
    kw = dict(x[2:].split('=', 1) for x in sys.argv[3:])
    lo = int(kw.get('start', 0))
    hi = int(kw.get('end', 1 << 30))
    src = kw.get('src')
    lines = {}
    if src:
        lines = {n + 1: l for n, l in enumerate(io.open(src, encoding='utf-8').read().splitlines())}
    for c in find_all(load_pyc(pyc), name):
        print('=== %s firstlineno=%d args=%s ===' % (c.co_name, c.co_firstlineno, c.co_varnames))
        last = None
        for i in dis.get_instructions(c):
            if i.opname == 'CACHE':
                continue
            ln = getattr(i, 'line_number', None) or getattr(i, 'starts_line', None)
            if ln is not None and ln != last:
                last = ln
                s = lines.get(last, '')
                print('      -- line %d: %s' % (last, s.strip()[:110]))
            if lo <= i.offset <= hi:
                print('  %5d %-30s %s' % (i.offset, i.opname, i.argrepr))
