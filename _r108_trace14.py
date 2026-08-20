"""Check if post-try blocks are collected and generated"""
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

result = gen._generate_try(try_region)
print(f"Type: {type(result).__name__}")
if isinstance(result, list):
    print(f"List length: {len(result)}")
    for i, item in enumerate(result):
        if isinstance(item, dict):
            print(f"  [{i}] type={item.get('type')}")
elif isinstance(result, dict):
    print(f"Dict type={result.get('type')}")
    print(f"Keys: {list(result.keys())}")

# Check if block 148 is in generated_blocks
block_148 = cfg.get_block_by_offset(148)
if block_148:
    print(f"\nblock 148 in generated_blocks: {block_148 in gen.generated_blocks}")
    print(f"block 148 in generated_offsets: {148 in gen.generated_offsets}")

# Check all top-level regions
print(f"\nTop-level regions:")
for r in gen.regions:
    if r.parent is None:
        print(f"  {type(r).__name__}: entry={r.entry.start_offset}")
