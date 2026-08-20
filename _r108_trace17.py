"""Add debug to _generate_try post-try loop"""
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

# Patch _generate_try to add debug output
import types

# Instead of patching, let me check the _post_try_blocks_r19n2 by
# examining what happens after _generate_try
# The key question: is block 148 in _post_try_blocks_r19n2?

# We can check by looking at whether _generate_try returns a list or dict
# If list, post-try stmts were appended. If dict, no post-try stmts.

result = gen._generate_try(try_region)
print(f"Result type: {type(result).__name__}")
if isinstance(result, list):
    print(f"List length: {len(result)}")
    for i, item in enumerate(result):
        if isinstance(item, dict):
            print(f"  [{i}] type={item.get('type')}")
elif isinstance(result, dict):
    print(f"Dict type={result.get('type')}")

# Check block 148 status
block_148 = cfg.get_block_by_offset(148)
print(f"\nblock 148 in generated_blocks: {block_148 in gen.generated_blocks}")

# Check if Region(entry=148) was generated
for r in gen.regions:
    if r.entry == block_148:
        rid = id(r)
        print(f"Region(entry=148) id={rid}")
        print(f"  in _generated_regions: {rid in gen._generated_regions}")
