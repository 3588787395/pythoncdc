#!/usr/bin/env python3
"""Debug BoolOpRegion for complex_expressions - check merge_block and blocks"""
import sys, marshal
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion, IfRegion

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

print("=== BoolOpRegions ===")
for r in analyzer.regions:
    if isinstance(r, BoolOpRegion):
        print(f"  BoolOpRegion@{r.entry.start_offset}:")
        print(f"    blocks: {[b.start_offset for b in r.blocks]}")
        print(f"    merge_block: {r.merge_block.start_offset if r.merge_block else 'None'}")
        print(f"    region_blocks: {[b.start_offset for b in r.region_blocks]}")
        # Show instructions in merge_block
        if r.merge_block:
            print(f"    merge_block instructions:")
            for i in r.merge_block.instructions:
                print(f"      {i.offset:4d}: {i.opname:30s} {i.argval}")
        # Show all blocks' instructions
        for b in r.blocks:
            if b != r.entry and b != r.merge_block:
                print(f"    block@{b.start_offset} instructions:")
                for i in b.instructions:
                    print(f"      {i.offset:4d}: {i.opname:30s} {i.argval}")

print("\n=== Block@220 details ===")
for b in list(cfg.blocks.values()):
    if b.start_offset == 220:
        print(f"  Block@220: succs={[s.start_offset for s in b.successors]}")
        for i in b.instructions:
            print(f"    {i.offset:4d}: {i.opname:30s} {i.argval}")
        region = analyzer.get_region_for_block(b)
        print(f"    region: {type(region).__name__}@{region.entry.start_offset}" if region else "    region: None")
