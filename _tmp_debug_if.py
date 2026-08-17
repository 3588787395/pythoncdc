#!/usr/bin/env python3
"""Debug IfRegion identification for complex_expressions"""
import sys
import marshal
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion

def load_pyc_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.loads(f.read())

orig_code = load_pyc_code('python_syntax_comprehensive_test.pyc')

for c in orig_code.co_consts:
    if hasattr(c, 'co_code') and c.co_name == 'complex_expressions':
        func_code = c
        break

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(func_code)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Show blocks around offset 312-356
blocks = list(cfg.blocks.values())
for block in sorted(blocks, key=lambda b: b.start_offset):
    if 280 <= block.start_offset <= 380:
        print(f"\nBlock@{block.start_offset}: succs={[s.start_offset for s in block.successors]}")
        for instr in block.instructions:
            print(f"  {instr.offset:4d}: {instr.opname:30s} {instr.argval}")

# Show all IfRegions
print("\n=== IfRegions ===")
for region in analyzer.regions:
    if isinstance(region, IfRegion):
        print(f"  IfRegion@{region.entry.start_offset}:")
        print(f"    then_blocks: {[b.start_offset for b in region.then_blocks] if region.then_blocks else 'None'}")
        print(f"    else_blocks: {[b.start_offset for b in region.else_blocks] if region.else_blocks else 'None'}")
        if hasattr(region, 'merge_block') and region.merge_block:
            print(f"    merge_block: {region.merge_block.start_offset}")
