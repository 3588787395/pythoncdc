"""Analyze repro_r11_06 region structure."""
import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')

import marshal
import types

# Load pyc
with open('.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_11/test_engineer/minimal_repros/repro_r11_06_try_except_finally_continue.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

# Build CFG
builder = CFGBuilder()
cfg = builder.build(code)

print(f"=== CFG blocks ({len(cfg.blocks)}) ===")
for blk in cfg.get_blocks_in_order():
    last = blk.instructions[-1] if blk.instructions else None
    last_str = f"{last.opname}→{last.argval}" if last else "None"
    succs = [s.start_offset for s in blk.successors]
    preds = [p.start_offset for p in blk.predecessors]
    print(f"  blk@{blk.start_offset} (end={blk.end_offset}): last={last_str}, succs={succs}, preds={preds}")
    for instr in blk.instructions:
        print(f"    {instr.offset:4d} {instr.opname:30s} {instr.argval}")
    print()

# Analyze regions
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

print(f"\n=== Regions ({len(regions)}) ===")
for i, r in enumerate(regions):
    blocks_str = [b.start_offset for b in r.blocks]
    print(f"  Region {i}: {type(r).__name__}: entry={r.entry.start_offset}, blocks={blocks_str}")
    if hasattr(r, 'then_blocks') and r.then_blocks:
        print(f"    then_blocks: {[b.start_offset for b in r.then_blocks]}")
    if hasattr(r, 'else_blocks') and r.else_blocks:
        print(f"    else_blocks: {[b.start_offset for b in r.else_blocks]}")
    if hasattr(r, 'body_blocks') and r.body_blocks:
        print(f"    body_blocks: {[b.start_offset for b in r.body_blocks]}")
    if hasattr(r, 'exception_blocks') and r.exception_blocks:
        print(f"    exception_blocks: {[b.start_offset for b in r.exception_blocks]}")
    if hasattr(r, 'cleanup_blocks') and r.cleanup_blocks:
        print(f"    cleanup_blocks: {[b.start_offset for b in r.cleanup_blocks]}")
    if hasattr(r, 'merge_block') and r.merge_block:
        print(f"    merge_block: {r.merge_block.start_offset}")
    if hasattr(r, 'header_block') and r.header_block:
        print(f"    header_block: {r.header_block.start_offset}")
    if hasattr(r, 'back_edge_block') and r.back_edge_block:
        print(f"    back_edge_block: {r.back_edge_block.start_offset}")
    if hasattr(r, 'parent') and r.parent:
        print(f"    parent: {type(r.parent).__name__}")
