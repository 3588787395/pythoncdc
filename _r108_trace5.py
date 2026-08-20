"""Debug full generation for repro_r2_07"""
import sys, marshal
sys.path.insert(0, '.')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from pycdc import decompile_pyc
import io

pyc_path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_07_finally_implicit_return.pyc'

# Decompile the full pyc
result = decompile_pyc(pyc_path)
print("=== Decompiled output ===")
print(result)
print("=== End ===")

# Now check the AST for the function
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

gen = RegionASTGenerator(cfg, ra)

# Generate all top-level regions
for r in ra.regions:
    if r.parent is None:
        ast = gen._generate_region(r)
        if ast:
            import json
            print(f"\n=== Region {type(r).__name__} AST ===")
            print(json.dumps(ast, indent=2, default=str)[:3000])
