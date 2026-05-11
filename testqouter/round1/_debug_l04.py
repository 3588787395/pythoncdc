import sys, os
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.basic_block import BasicBlock
from core.cfg import LoopRegion
import py_compile
import dis

py_compile.compile('testqouter/round1/test_l04_while_break.py', 'testqouter/round1/tmp.pyc')
code = __import__('marshal').load(open('testqouter/round1/tmp.pyc', 'rb'))
code = code[12:]  # skip header
co = __import__('marshal').loads(code)

builder = CFGBuilder()
cfg = builder.build(co)

print("=== CFG BLOCKS ===")
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    print(f"  Block offset={b.start_offset}, succs={[s.start_offset for s in b.successors]}, preds={[p.start_offset for p in b.predecessors]}")
    for inst in b.instructions:
        print(f"    {inst.offset:4d} {inst.opname:30s} {inst.argrepr if inst.argrepr else ''}")
    print()

analyzer = RegionAnalyzer(cfg, co)
analyzer.analyze()

print("=== REGIONS ===")
for r in analyzer.regions:
    rtype = r.__class__.__name__
    blocks_str = [b.start_offset for b in r.blocks]
    if isinstance(r, LoopRegion):
        print(f"  {rtype}: blocks={blocks_str}")
        print(f"    header_block={r.header_block.start_offset if r.header_block else None}")
        print(f"    back_edge_block={r.back_edge_block.start_offset if r.back_edge_block else None}")
        print(f"    body_blocks={[b.start_offset for b in r.body_blocks]}")
        print(f"    condition_block={r.condition_block.start_offset if r.condition_block else None}")
    else:
        print(f"  {rtype}: blocks={blocks_str}")
