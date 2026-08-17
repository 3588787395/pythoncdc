#!/usr/bin/env python3
"""Debug: check what _find_loop_else returns for the for-else in control_flow_examples"""
import sys
import marshal
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, RegionType

def load_pyc_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.loads(f.read())

orig_code = load_pyc_code('python_syntax_comprehensive_test.pyc')

# Find control_flow_examples
for c in orig_code.co_consts:
    if hasattr(c, 'co_code') and c.co_name == 'control_flow_examples':
        func_code = c
        break

# Build CFG
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(func_code)

# Build region analyzer
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find LoopRegions
for region in analyzer.regions:
    if isinstance(region, LoopRegion):
        print(f"\n=== LoopRegion at offset {region.header_block.start_offset} ===")
        print(f"  region_type: {region.region_type}")
        print(f"  header: {region.header_block.start_offset}")
        if region.else_blocks:
            print(f"  else_blocks: {[b.start_offset for b in region.else_blocks]}")
        else:
            print(f"  else_blocks: None (empty)")
        if region.break_blocks:
            print(f"  break_blocks: {[b.start_offset for b in region.break_blocks]}")
        else:
            print(f"  break_blocks: None (empty)")
        if region.body_blocks:
            print(f"  body_blocks: {[b.start_offset for b in region.body_blocks]}")
        if region.back_edge_block:
            print(f"  back_edge_block: {region.back_edge_block.start_offset}")
        print(f"  has_break: {region.has_break}")
