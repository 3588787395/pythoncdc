# -*- coding: utf-8 -*-
"""Trace _generate_ternary / _build_ternary_boolop_condition during a real generate().
usage: trace_ternary.py <pyc> <fn> [nested-firstlineno]"""
import io, marshal, os, sys, types
sys.path.insert(0, r'F:/Downloads/pythoncdc-main'); sys.path.insert(0, r'D:/Temp/opencode/r67gate/diag6')
os.chdir(r'F:/Downloads/pythoncdc-main'); sys.stdout.reconfigure(encoding='utf-8')
import regdump
O = lambda b: getattr(b, 'start_offset', None)
pyc, fn = sys.argv[1], sys.argv[2]
want = int(sys.argv[3]) if len(sys.argv) > 3 else None
root = regdump.load_pyc(pyc)
codes = [c for c in regdump.walk(root, []) if c.co_name == fn]
sel = [k for c in codes for k in c.co_consts if isinstance(k, types.CodeType) and (not want or k.co_firstlineno == want)] or codes
from core.cfg import build_cfg
import core.cfg.region_ast_generator as G
gt = G.RegionASTGenerator._generate_ternary
bt = G.RegionASTGenerator._build_ternary_boolop_condition
def wgt(self, region, skip_store_targets=None):
    ch = getattr(region, 'condition_chain_blocks', None) or []
    print('>> _generate_ternary entry=%s chain=%s mc=%s vt=%s ct=%s cond=%s true=%s false=%s merge=%s' % (
        O(region.entry), [O(x[0]) if isinstance(x, tuple) else O(x) for x in ch], getattr(region,'merge_context',None),
        getattr(region,'value_target',None), getattr(region,'container_type',None),
        O(region.condition_block), O(getattr(region,'true_value_block',None)), O(getattr(region,'false_value_block',None)), O(getattr(region,'merge_block',None))))
    r = gt(self, region, skip_store_targets)
    print('<< -> %s' % (str(r)[:300]))
    return r
def wbt(self, region, *a, **k):
    ch = getattr(region, 'condition_chain_blocks', None) or []
    print('   _build_ternary_boolop_condition entry=%s chain=%s' % (O(region.entry), [O(x[0]) if isinstance(x, tuple) else O(x) for x in ch]))
    r = bt(self, region, *a, **k)
    print('   <- %s' % str(r)[:200])
    return r
G.RegionASTGenerator._generate_ternary = wgt
G.RegionASTGenerator._build_ternary_boolop_condition = wbt
for code in sel:
    print('##### %s@L%d' % (code.co_name, code.co_firstlineno))
    cfg = build_cfg(code)
    gen = G.RegionASTGenerator(cfg)
    d = gen.generate()
    import ast
    body = d['body'] if isinstance(d, dict) else d
    mod = ast.Module(body=[n for n in (body if isinstance(body, list) else [body]) if isinstance(n, ast.AST)], type_ignores=[])
    print('  RESULT:', ast.unparse(mod)[:400])
