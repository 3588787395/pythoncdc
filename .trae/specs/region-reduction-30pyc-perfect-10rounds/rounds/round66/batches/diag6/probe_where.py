# -*- coding: utf-8 -*-
"""diag6 read-only: print the call stack at the moment a generator helper is invoked on
an instruction list that starts at a given offset (finds the owning emitter).

usage: python -X utf8 probe_where.py <pyc> <co_name> <first_offset> [meth1,meth2,...]
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


if __name__ == '__main__':
    pyc, co_name, first = sys.argv[1], sys.argv[2], int(sys.argv[3])
    meths = (sys.argv[4].split(',') if len(sys.argv) > 4 else
             ['_build_store_statement', '_build_statement', '_generate_stmts_from_instrs',
              '_build_effective_stmts'])
    import core.cfg.region_ast_generator as G
    import traceback

    for m in meths:
        orig = getattr(G.RegionASTGenerator, m)

        def make(m, orig):
            def w(self, *a, **k):
                if getattr(self.cfg, 'name', None) == co_name:
                    for x in a:
                        if isinstance(x, (list, tuple)) and x and hasattr(x[0], 'offset') \
                                and x[0].offset == first:
                            print('### %s  arg=%s..%s  block=%s'
                                  % (m, x[0].offset, x[-1].offset,
                                     getattr(k.get('block'), 'start_offset', None)))
                            for fr in traceback.extract_stack()[:-1][::-1][:14]:
                                if 'region_ast_generator' in (fr.filename or ''):
                                    print('    %s:%d %s  |  %s'
                                          % (os.path.basename(fr.filename), fr.lineno,
                                             fr.name, (fr.line or '')[:90]))
                            sys.stdout.flush()
                            r = orig(self, *a, **k)
                            print('    -> %s' % (
                                [s.get('type') if isinstance(s, dict) else type(s).__name__
                                 for s in r] if isinstance(r, list) else type(r).__name__))
                            return r
                return orig(self, *a, **k)
            return w

        setattr(G.RegionASTGenerator, m, make(m, orig))

    import pycdc
    txt = pycdc.decompile_pyc(pyc)
    io.open(r'D:/Temp/opencode/r66gate/diag6/logs/probe_where_product.py', 'w',
            encoding='utf-8').write(txt)
