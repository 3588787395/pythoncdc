"""Check post-try block collection details"""
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

# Manually replicate the post-try collection logic
# to check if block 148 is collected
block_148 = cfg.get_block_by_offset(148)

# Check finally_copy_blocks successors
_known_struct = set()
for b in try_region.try_blocks: _known_struct.add(b.start_offset)
for b in try_region.else_blocks: _known_struct.add(b.start_offset)
for b in try_region.finally_blocks: _known_struct.add(b.start_offset)
for et, en, hbs in try_region.except_handlers:
    for b in hbs: _known_struct.add(b.start_offset)
_known_struct.update(try_region.finally_copy_blocks.keys())

print(f"_known_struct: {_known_struct}")
print(f"148 in _known_struct: {148 in _known_struct}")

# Check fc block 114's successors
fc_block = cfg.get_block_by_offset(114)
if fc_block:
    for succ in fc_block.successors:
        print(f"fc 114 -> succ {succ.start_offset}")
        print(f"  succ.start_offset in _known_struct: {succ.start_offset in _known_struct}")
        print(f"  succ == block_148: {succ is block_148}")

# Now call _generate_try and check result
result = gen._generate_try(try_region)
print(f"\nresult type: {type(result).__name__}")
if isinstance(result, dict):
    print(f"result keys: {list(result.keys())}")
elif isinstance(result, list):
    print(f"result length: {len(result)}")
    for i, item in enumerate(result):
        if isinstance(item, dict):
            print(f"  [{i}] type={item.get('type')}")

# Check if block 148 was collected as post-try
# We can't directly check _post_try_blocks_r19n2, but we can check
# if the result is a list (which would include post-try stmts)
print(f"\nblock 148 in generated_blocks: {block_148 in gen.generated_blocks}")
