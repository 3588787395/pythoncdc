# -*- coding: utf-8 -*-
"""Run the LIVE region pipeline on a NESTED code object of a named function and print
the emitted AST (unparse) + the region tree. usage: probe_genexpr.py <pyc> <parent> [firstlineno]"""
import ast, io, marshal, os, sys, types
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
os.chdir(r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')

def load_pyc(path):
    d = io.open(path, 'rb').read()
    for off in (16, 12, 8):
        try: return marshal.loads(d[off:])
        except Exception: pass
    raise SystemExit('bad pyc')

def walk(c, o):
    o.append(c)
    for k in c.co_consts:
        if isinstance(k, types.CodeType): walk(k, o)
    return o

pyc, parent = sys.argv[1], sys.argv[2]
want = int(sys.argv[3]) if len(sys.argv) > 3 else None
codes = [c for c in walk(load_pyc(pyc), []) if c.co_name == parent]
code = codes[0]
gens = [k for k in code.co_consts if isinstance(k, types.CodeType)]
for g in gens:
    if want and g.co_firstlineno != want: continue
    print('##### nested %s firstlineno=%d free=%s var=%s' % (g.co_name, g.co_firstlineno, g.co_freevars, g.co_varnames))
    from core.cfg import build_cfg
    from core.cfg.region_ast_generator import RegionASTGenerator
    cfg = build_cfg(g)
    gen = RegionASTGenerator(cfg)
    regions = gen.region_analyzer.analyze()
    print('  blocks=%d regions=%d' % (len(cfg.blocks), len(regions)))
    for r in sorted(regions, key=lambda x: getattr(x.entry,'start_offset',0) or 0):
        print('   %-22s entry=%-5s blocks=%s' % (type(r).__name__, getattr(r.entry,'start_offset',None),
              [getattr(b,'start_offset',None) for b in (r.blocks or [])]))
    for r in sorted(regions, key=lambda x: getattr(x.entry,'start_offset',0) or 0):
        print('   CHILD %-16s entry=%-5s -> %s' % (type(r).__name__, getattr(r.entry,'start_offset',None),
              ['%s@%s'%(type(c).__name__, getattr(c.entry,'start_offset',None)) for c in (r.children or [])]))
    d = gen.generate()
    print('  generate() ->', type(d))
    def nodes(x):
        if isinstance(x, dict): return x.get('body') or list(x.values())
        return x
    try:
        body = d['body'] if isinstance(d, dict) else d
        mod = ast.Module(body=[n for n in (body if isinstance(body, list) else [body]) if isinstance(n, ast.AST)], type_ignores=[])
        print('  --- AST ---'); print(ast.unparse(mod)[:2500])
    except Exception as e:
        print('  unparse failed', e)
    print('  --- REPR ---'); print(repr(d)[:2500])
