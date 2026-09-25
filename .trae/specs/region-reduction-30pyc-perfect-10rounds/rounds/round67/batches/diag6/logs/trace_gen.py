# -*- coding: utf-8 -*-
"""Trace every _generate*/_build* call the live generator makes for one code object.
usage: trace_gen.py <pyc> <fn> [depth]"""
import ast, io, marshal, os, sys, types
sys.path.insert(0, r'F:/Downloads/pythoncdc-main'); sys.path.insert(0, r'D:/Temp/opencode/r67gate/diag6')
os.chdir(r'F:/Downloads/pythoncdc-main'); sys.stdout.reconfigure(encoding='utf-8')
import regdump
O = lambda b: getattr(b, 'start_offset', None)
pyc, fn = sys.argv[1], sys.argv[2]
root = regdump.load_pyc(pyc)
codes = [c for c in regdump.walk(root, []) if c.co_name == fn]
code = codes[0]
from core.cfg import build_cfg
import core.cfg.region_ast_generator as G
TARGETS = [n for n in dir(G.RegionASTGenerator)
           if (n.startswith('_generate') or n.startswith('_build') or n.startswith('_emit')) and callable(getattr(G.RegionASTGenerator, n))]
depth = [0]
MAXD = int(sys.argv[3]) if len(sys.argv) > 3 else 6
def summ(r):
    if isinstance(r, dict): return 'dict:%s' % r.get('type')
    if isinstance(r, list): return 'list[%d]%s' % (len(r), summ(r[0]) if r else '')
    return type(r).__name__
def wrap(name, f):
    def w(self, *a, **k):
        reg = a[0] if a else None
        tag = ''
        if hasattr(reg, 'entry'):
            tag = '%s@%s' % (type(reg).__name__, O(reg.entry))
        elif isinstance(reg, list) and reg and hasattr(reg[0], 'start_offset'):
            tag = 'blocks=%s' % [O(x) for x in reg][:8]
        elif isinstance(reg, str):
            tag = repr(reg)[:30]
        pad = '  ' * depth[0]
        print('%s%s %s' % (pad, name, tag))
        d = depth[0] + 1
        r = f(self, *a, **k)
        if d <= MAXD:
            print('%s%s -> %s' % ('  ' * (d - 1), '=' * max(0, 20 - len(name)), summ(r)[:90]))
        return r
    return w
for n in TARGETS:
    setattr(G.RegionASTGenerator, n, wrap(n, getattr(G.RegionASTGenerator, n)))
cfg = build_cfg(code)
gen = G.RegionASTGenerator(cfg)
d = gen.generate()
body = d['body'] if isinstance(d, dict) else d
mod = ast.Module(body=[n for n in (body if isinstance(body, list) else [body]) if isinstance(n, ast.AST)], type_ignores=[])
print('===== RESULT =====')
print(ast.unparse(mod)[:1200])
