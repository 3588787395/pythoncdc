"""Debug _generate_try for repro_r2_07 - full AST output"""
import sys, marshal, types, json
sys.path.insert(0, '.')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

pyc_path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_07_finally_implicit_return.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

func_code = None
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'test_finally_implicit_return':
        func_code = c
        break

cfg = build_cfg(func_code)
ra = RegionAnalyzer(cfg)
ra.analyze()

try_region = None
for r in ra.regions:
    if hasattr(r, 'has_finally'):
        try_region = r
        break

gen = RegionASTGenerator(cfg, ra)
result = gen._generate_try(try_region)
print(json.dumps(result, indent=2, default=str))
