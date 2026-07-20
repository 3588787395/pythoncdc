"""Debug the if87 test case to see CFG structure."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

source = """if a > 0:
    while a > 10:
        a = a - 1"""

import dis
import types

code = compile(source, '<test>', 'exec')
print("=== BYTECODE ===")
dis.dis(code)
print()

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole

cfg = CFGBuilder().build_cfg(code)
print("=== BLOCKS ===")
for block in sorted(cfg.blocks, key=lambda b: b.start_offset):
    print(f"\nBlock @{block.start_offset}")
    print(f"  Last instr: {block.get_last_instruction()}")
    print(f"  Successors: {[s.start_offset for s in block.successors]}")
    print(f"  Predecessors: {[p.start_offset for p in block.predecessors]}")
    print(f"  Instructions:")
    for i in block.instructions:
        print(f"    {i.opname} {i.argval}")

print()
print("=== BACK EDGES ===")
from core.cfg.loop_analyzer import LoopAnalyzer
la = LoopAnalyzer(cfg)
for src, tgt in la.back_edges:
    print(f"  {src.start_offset} -> {tgt.start_offset}")

print()
print("=== REGIONS ===")
ra = RegionAnalyzer(cfg)
ra.analyze()
for r in ra.regions:
    print(f"  {type(r).__name__} blocks={[b.start_offset for b in r.blocks]}")
    if hasattr(r, 'header_block'):
        print(f"    header={r.header_block.start_offset}")
    if hasattr(r, 'condition_block') and r.condition_block:
        print(f"    condition_block={r.condition_block.start_offset}")
print()

print("=== BLOCK ROLES ===")
for offset, role in sorted(ra.block_roles.items()):
    print(f"  @{offset}: {role}")
