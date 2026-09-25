# -*- coding: utf-8 -*-
"""side-by-side raw instruction window for one function: ORIG from .pyc vs DECOMP from the *OK.py.

usage: python -X utf8 logs/side.py <pyc> <okpy> <func> --lo=N --hi=N [--which=both|orig|dec]
"""
import dis
import io
import marshal
import os
import sys
import types

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(HERE)


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


def instrs(code):
    return [(i.opname, str(i.argrepr), i.offset, getattr(i, 'line_number', None))
            for i in dis.get_instructions(code) if i.opname != 'CACHE']


def show(tag, seq, lo, hi, lastline):
    print('--- %s ---' % tag)
    for op, arg, off, ln in seq:
        if not (lo <= off <= hi):
            continue
        m = '' if ln == lastline else ' [L%s]' % ln
        print('  %5d %-30s %s%s' % (off, op, arg[:70], m))
    return lastline


if __name__ == '__main__':
    pyc, okpy, name = sys.argv[1], sys.argv[2], sys.argv[3]
    kw = dict(x[2:].split('=', 1) for x in sys.argv[4:])
    lo, hi = int(kw.get('lo', 0)), int(kw.get('hi', 1 << 30))
    which = kw.get('which', 'both')
    oc = [c for c in walk(load_pyc(pyc), []) if c.co_name == name]
    assert len(oc) == 1, len(oc)
    dc = [c for c in walk(compile(io.open(okpy, encoding='utf-8').read(), okpy, 'exec'), [])
          if c.co_name == name]
    assert len(dc) == 1, len(dc)
    if which in ('both', 'orig'):
        show('ORIG %s' % name, instrs(oc[0]), lo, hi, None)
    if which in ('both', 'dec'):
        show('DECOMP %s' % name, instrs(dc[0]), lo, hi, None)
