#!/usr/bin/env python3
"""Detailed CFG block analysis for control_flow_examples"""
import sys
import dis
import marshal
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion

def load_pyc_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.loads(f.read())

orig_code = load_pyc_code('python_syntax_comprehensive_test.pyc')

for c in orig_code.co_consts:
    if hasattr(c, 'co_code') and c.co_name == 'control_flow_examples':
        func_code = c
        break

# Build CFG
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(func_code)

# Print all blocks - cfg.blocks might be a dict
print(f"cfg.blocks type: {type(cfg.blocks)}")
if isinstance(cfg.blocks, dict):
    blocks = list(cfg.blocks.values())
else:
    blocks = list(cfg.blocks)

print(f"Number of blocks: {len(blocks)}")
print("=== All CFG blocks ===")
for block in sorted(blocks, key=lambda b: b.start_offset):
    instrs = [(i.offset, i.opname, i.argval) for i in block.instructions]
    succs = [s.start_offset for s in block.successors]
    print(f"  Block@{block.start_offset}: succs={succs}")
    for off, name, arg in instrs:
        print(f"    {off:4d}: {name:30s} {arg}")

# Build region analyzer
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print("\n=== LoopRegions ===")
for region in analyzer.regions:
    if isinstance(region, LoopRegion):
        print(f"\n  LoopRegion@{region.header_block.start_offset}:")
        print(f"    region_type: {region.region_type}")
        print(f"    else_blocks: {[b.start_offset for b in region.else_blocks] if region.else_blocks else 'None'}")
        print(f"    break_blocks: {[b.start_offset for b in region.break_blocks] if region.break_blocks else 'None'}")
        print(f"    body_blocks: {[b.start_offset for b in region.body_blocks]}")
        if hasattr(region, 'natural_exit') and region.natural_exit:
            print(f"    natural_exit: {region.natural_exit.start_offset}")
