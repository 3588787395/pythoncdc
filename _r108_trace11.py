"""Check if block 18 is already generated when else logic runs"""
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
gen = RegionASTGenerator(cfg)
gen.regions = gen.region_analyzer.analyze()

try_region = None
for r in gen.regions:
    if hasattr(r, 'has_finally'):
        try_region = r
        break

# Check else_blocks before _generate_try
print(f"else_blocks: {[b.start_offset for b in try_region.else_blocks]}")
for eb in try_region.else_blocks:
    print(f"  block {eb.start_offset} in generated_blocks: {eb in gen.generated_blocks}")
    print(f"  instructions: {[(i.opname, i.argval) for i in eb.instructions]}")
    print(f"  successors: {[s.start_offset for s in eb.successors]}")

# Now call _generate_try and check
result = gen._generate_try(try_region)
print(f"\nresult has orelse: {'orelse' in result}")
if 'orelse' in result:
    print(f"orelse: {json.dumps(result['orelse'], default=str)}")
else:
    # Check if else_blocks were marked generated
    for eb in try_region.else_blocks:
        print(f"  block {eb.start_offset} in generated_blocks after: {eb in gen.generated_blocks}")
