"""Check final_integration_test CFG regions"""
import sys, marshal
sys.path.insert(0, '.')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

pyc_path = 'decompiler_test_comprehensive.cpython-311.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'DataProcessor':
        for cc in c.co_consts:
            if hasattr(cc, 'co_name') and cc.co_name == 'final_integration_test':
                func_code = cc
                break
        break

cfg = build_cfg(func_code)
gen = RegionASTGenerator(cfg)

# Print top-level regions
top_level = [r for r in gen.regions if r.parent is None]
print("=== Top-level regions ===")
for region in top_level:
    print(f"  {type(region).__name__}: entry={region.entry_block.start_offset}")
    if hasattr(region, 'try_blocks'):
        print(f"    try_blocks: {[b.start_offset for b in region.try_blocks]}")
    if hasattr(region, 'handler_blocks'):
        print(f"    handler_blocks: {[b.start_offset for b in region.handler_blocks]}")
    if hasattr(region, 'else_blocks'):
        print(f"    else_blocks: {[b.start_offset for b in region.else_blocks]}")
    if hasattr(region, 'finally_blocks'):
        print(f"    finally_blocks: {[b.start_offset for b in region.finally_blocks]}")
    if hasattr(region, 'finally_copy_blocks'):
        print(f"    finally_copy_blocks: {list(region.finally_copy_blocks.keys())}")
    if hasattr(region, 'blocks'):
        print(f"    blocks: {[b.start_offset for b in region.blocks]}")

# Print all blocks
print("\n=== All blocks ===")
for block in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
    succs = [s.start_offset for s in block.successors]
    print(f"  block {block.start_offset}: succs={succs}")
