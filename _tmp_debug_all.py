#!/usr/bin/env python3
"""Debug ALL blocks and regions for complex_expressions"""
import sys, marshal
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

blocks = list(cfg.blocks.values())
print("=== ALL blocks ===")
for block in sorted(blocks, key=lambda b: b.start_offset):
    succs = [s.start_offset for s in block.successors]
    region = analyzer.get_region_for_block(block)
    rinfo = type(region).__name__ if region else "None"
    print(f"  @{block.start_offset}: succs={succs} region={rinfo}")
    for i in block.instructions:
        print(f"    {i.offset:4d}: {i.opname:30s} {i.argval}")

print("\n=== Regions ===")
for r in analyzer.regions:
    print(f"  {type(r).__name__}@{r.entry.start_offset}")
