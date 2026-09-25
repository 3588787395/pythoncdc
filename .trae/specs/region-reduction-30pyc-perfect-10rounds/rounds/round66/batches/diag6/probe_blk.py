# -*- coding: utf-8 -*-
"""diag6 read-only: wrap EVERY RegionASTGenerator/RegionAnalyzer method and log those
that touch a given basic block, with the statement types each returns.

usage: python -X utf8 probe_blk.py <pyc> <co_name> <block_start_offset> [--analyzer]
"""
import io
import marshal
import os
import sys
import types

REPO = r'F:/Downloads/pythoncdc-main'
sys.path.insert(0, REPO)
os.chdir(REPO)
sys.stdout.reconfigure(encoding='utf-8')


def load_pyc(path):
    data = io.open(path, 'rb').read()
    for off in (16, 12, 8):
        try:
            return marshal.loads(data[off:])
        except Exception:
            continue
    raise SystemExit('cannot unmarshal')


def walk(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, out)
    return out


def stmt_names(r):
    if isinstance(r, list):
        return '[' + ','.join((x.get('type') or x.get('kind')) if isinstance(x, dict) else '?' for x in r) + ']'
    if isinstance(r, dict):
        return '{' + str(r.get('type') or r.get('kind')) + '}'
    if r is None:
        return 'None'
    return type(r).__name__


def offs_of(instrs):
    try:
        return '%s..%s' % (instrs[0].offset, instrs[-1].offset)
    except Exception:
        return '?'


def wrap_cls(cls, co_name, blk_off, tag):
    n = 0
    for attr in dir(cls):
        if attr.startswith('__'):
            continue
        try:
            f = getattr(cls, attr)
        except Exception:
            continue
        if not callable(f) or not hasattr(f, '__code__'):
            continue
        n += 1

        def make(attr, f):
            def w(self, *a, **k):
                mine = any(getattr(x, 'start_offset', None) == blk_off for x in a)
                mine = mine or any(getattr(getattr(x, 'entry', None), 'start_offset', None) == blk_off
                                   for x in a)
                if not mine:
                    for v in k.values():
                        if getattr(v, 'start_offset', None) == blk_off:
                            mine = True
                if getattr(getattr(self, 'cfg', None), 'name', None) != co_name:
                    mine = False
                if mine:
                    r = f(self, *a, **k)
                    d = []
                    for x in a:
                        if hasattr(x, 'start_offset'):
                            d.append('blk=%s' % getattr(x, 'start_offset', None))
                        elif hasattr(x, 'entry'):
                            d.append('%s@%s' % (type(x).__name__, getattr(getattr(x, 'entry', None),
                                                                          'start_offset', None)))
                        elif isinstance(x, (list, tuple)) and x and hasattr(x[0], 'offset'):
                            d.append('instrs(%s)' % offs_of(x))
                        elif isinstance(x, (list, tuple)):
                            d.append('%s(%d)' % (type(x).__name__, len(x)))
                        elif isinstance(x, (int, str, bool)) or x is None:
                            d.append(repr(x))
                    print('%s.%-46s %s -> %s' % (tag, attr, ' '.join(d)[:120], stmt_names(r)[:160]))
                    sys.stdout.flush()
                    return r
                return f(self, *a, **k)
            return w

        setattr(cls, attr, make(attr, f))
    print('# %s wrapped %d callables' % (tag, n))


if __name__ == '__main__':
    pyc, co_name, blk = sys.argv[1], sys.argv[2], int(sys.argv[3])
    import core.cfg.region_ast_generator as G
    import core.cfg.region_analyzer as A
    wrap_cls(G.RegionASTGenerator, co_name, blk, 'GEN')
    if '--analyzer' in sys.argv:
        wrap_cls(A.RegionAnalyzer, co_name, blk, 'ANA')
    import pycdc
    txt = pycdc.decompile_pyc(pyc)
    io.open(r'D:/Temp/opencode/r66gate/diag6/logs/probe_blk_product.py', 'w',
            encoding='utf-8').write(txt)
