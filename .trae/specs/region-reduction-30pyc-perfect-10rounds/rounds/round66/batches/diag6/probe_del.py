# -*- coding: utf-8 -*-
"""diag6 read-only instrumentation probe: run the REAL repo pipeline on a pyc and log
which generator entry points see a given opcode inside a given code object.

usage: python -X utf8 probe_del.py <pyc> <co_name> <opname> [--m=method1,method2]
No repo writes: monkey-patches live objects in memory only.
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
    pyc, co_name, opname = sys.argv[1], sys.argv[2], sys.argv[3]
    kw = dict(x[2:].split('=', 1) for x in sys.argv[4:])
    meths = kw.get('m', '_generate_stmts_from_instrs,_build_delete_stmt,'
                             '_build_effective_stmts,_generate_block_statements_body').split(',')
    import core.cfg.region_ast_generator as G
    hits = []

    def names_of(r):
        if isinstance(r, list):
            return [x.get('type') if isinstance(x, dict) else '?' for x in r]
        return type(r).__name__

    for m in meths:
        orig = getattr(G.RegionASTGenerator, m, None)
        if orig is None:
            print('!! no method', m)
            continue

        def make(m, orig):
            def w(self, *a, **k):
                try:
                    cfgname = getattr(self.cfg, 'name', None) or getattr(self.cfg, 'code_object', None)
                    cfgname = getattr(cfgname, 'co_name', cfgname)
                except Exception:
                    cfgname = '?'
                interesting = (cfgname == co_name)
                if interesting:
                    blk = next((x for x in a if hasattr(x, 'start_offset')), None)
                    ins = next((x for x in a if isinstance(x, (list, tuple)) and x
                                and hasattr(x[0], 'opname')), None)
                    ops = [getattr(i, 'opname', '?') for i in ins] if ins is not None else []
                    has = opname in ops
                    if has or blk is not None:
                        r = orig(self, *a, **k)
                        offs = [getattr(i, 'offset', None) for i in ins] if ins is not None else []
                        print('%-34s blk=%s n=%d hasOP=%s offs=%s..%s -> %s'
                              % (m, getattr(blk, 'start_offset', None), len(ops), has,
                                 offs[0] if offs else None, offs[-1] if offs else None,
                                 names_of(r)))
                        sys.stdout.flush()
                        return r
                return orig(self, *a, **k)
            return w

        setattr(G.RegionASTGenerator, m, make(m, orig))

    import pycdc
    txt = pycdc.decompile_pyc(pyc)
    sys.stderr.write(str(compile))
    io.open(os.path.join(r'D:/Temp/opencode/r66gate/diag6', 'logs/probe_del_product.py'),
            'w', encoding='utf-8').write(txt)
    print('--- product written, del lines:')
    for i, l in enumerate(txt.splitlines(), 1):
        if 'del ' in l or co_name in l:
            print(i, l.rstrip()[:120])
