"""Check top_level_regions"""
import sys, marshal, json
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
regions = ra.analyze()

gen = RegionASTGenerator(cfg)
gen.regions = regions
gen.region_analyzer = ra

# Now manually call _generate_try on the TryExceptRegion
try_region = None
for r in regions:
    if hasattr(r, 'has_finally'):
        try_region = r
        break

result = gen._generate_try(try_region)
print(f"orelse in result: {'orelse' in result}")
if 'orelse' in result:
    print(f"orelse: {json.dumps(result['orelse'], default=str)}")

# Now call generate() which re-analyzes
gen2 = RegionASTGenerator(cfg)
ast2 = gen2.generate()
for node in ast2.get('body', []):
    if isinstance(node, dict) and node.get('type') == 'Try':
        print(f"\ngenerate() Try has orelse: {'orelse' in node}")
        print(f"generate() Try keys: {list(node.keys())}")
