"""Debug bool11 to see what _has_back_edge_recheck_exit sees."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

source = """while not done and has_data():
    process()"""

from core.cfg.region_analyzer import RegionAnalyzer, FORWARD_CONDITIONAL_JUMP_OPS, LoopRegion
from core.cfg.cfg_builder import CFGBuilder

code = compile(source, '<test>', 'exec')

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print("=== BLOCKS ===")
all_blocks = sorted(cfg.get_blocks_in_order(), key=lambda b: b.start_offset)
for block in all_blocks:
    last = block.get_last_instruction()
    print(f"Block @{block.start_offset} last={last.opname if last else None}({last.argval if last else None})")
    print(f"  succs={[s.start_offset for s in block.successors]}")
    print(f"  preds={[p.start_offset for p in block.predecessors]}")

print()
print("=== REGIONS ===")
for r in analyzer.regions:
    print(f"  {type(r).__name__} blocks={[b.start_offset for b in r.blocks]}")
    if hasattr(r, 'header_block'):
        print(f"    header={r.header_block.start_offset}")
    if hasattr(r, 'body_blocks'):
        print(f"    body_blocks={[b.start_offset for b in r.body_blocks]}")
    if hasattr(r, 'condition_block') and r.condition_block:
        print(f"    condition_block={r.condition_block.start_offset}")

# Now manually check _has_back_edge_recheck_exit
print()
print("=== MANUAL CHECK ===")
for r in analyzer.regions:
    if isinstance(r, LoopRegion):
        body = r.body_blocks
        header = r.header_block
        print(f"LoopRegion body={[b.start_offset for b in body]} header={header.start_offset}")
        for b in body:
            b_last = b.get_last_instruction()
            if b_last and b_last.opname in FORWARD_CONDITIONAL_JUMP_OPS and b_last.argval is not None:
                b_target = cfg.get_block_by_offset(b_last.argval)
                is_trivial = analyzer._is_trivial_return_block(b_target) if b_target else False
                is_header = b_target is header
                in_body = b_target in body
                print(f"  Block @{b.start_offset}: {b_last.opname} -> @{b_target.start_offset if b_target else None}")
                print(f"    is_trivial_return={is_trivial} is_header={is_header} in_body={in_body}")
