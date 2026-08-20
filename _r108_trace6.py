"""Check _generate_try return type"""
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
ra.analyze()

try_region = None
for r in ra.regions:
    if hasattr(r, 'has_finally'):
        try_region = r
        break

gen = RegionASTGenerator(cfg, ra)
result = gen._generate_try(try_region)
print(f"Return type: {type(result)}")
if isinstance(result, list):
    print(f"List length: {len(result)}")
    for i, item in enumerate(result):
        print(f"  [{i}] type={type(item).__name__}, type field={item.get('type') if isinstance(item, dict) else 'N/A'}")
else:
    print(f"Dict type field: {result.get('type') if isinstance(result, dict) else 'N/A'}")
    # Check if orelse is present
    if isinstance(result, dict):
        print(f"  has orelse: {'orelse' in result}")
        if 'orelse' in result:
            print(f"  orelse: {json.dumps(result['orelse'], default=str)}")
