#!/usr/bin/env python3
"""Debug: dump CFG blocks for async/generator functions"""
import sys
import os
import dis
import marshal
import struct
import types

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

def load_pyc_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        magic = f.read(4)
        flags = struct.unpack('<I', f.read(4))[0]
        f.read(8)
        code = marshal.load(f)
    return code

orig_code = load_pyc_code('python_syntax_comprehensive_test.pyc')

# Find target code objects
for const in orig_code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name in ('simple_generator', 'simple_coroutine', 'multiple_coroutines'):
        print(f"\n{'='*60}")
        print(f"Function: {const.co_name}")
        print(f"{'='*60}")
        
        # Build CFG
        builder = CFGBuilder()
        cfg = builder.build(const)
        
        print(f"\nCFG blocks ({len(cfg.blocks)}):")
        for offset, block in sorted(cfg.blocks.items()):
            preds = [str(p.start_offset) for p in block.predecessors]
            succs = [str(s.start_offset) for s in block.successors]
            print(f"  Block {block.start_offset}: preds={preds}, succs={succs}")
            for instr in block.instructions:
                print(f"    {instr.offset:4d}: {instr.opname:30s} {instr.argval}")
        
        # Analyze regions
        analyzer = RegionAnalyzer(cfg)
        regions = analyzer.analyze()
        
        print(f"\nMetadata:")
        for k, v in analyzer.metadata.items():
            print(f"  {k}: {v}")
        
        print(f"\nRegions ({len(regions)}):")
        for r in regions:
            print(f"  {type(r).__name__}: entry={r.entry_block.start_offset if hasattr(r, 'entry_block') and r.entry_block else 'None'}")
            if hasattr(r, 'blocks'):
                print(f"    blocks: {[b.start_offset for b in r.blocks]}")
        
        print(f"\nblock_to_region:")
        for block, region in sorted(analyzer.block_to_region.items(), key=lambda x: x[0].start_offset):
            rname = type(region).__name__ if region else 'None'
            print(f"  Block {block.start_offset}: {rname}")
