"""R30 调试 get_block_stocks 的区域分析 - 循环体首语句丢失"""
import sys
import dis
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, IfRegion

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

target = None
for const in code_obj.co_consts:
    if isinstance(const, type(code_obj)) and const.co_name == 'get_block_stocks':
        target = const
        break

print(f"Function: {target.co_name}")
print(f"co_code length: {len(target.co_code)}")

# Disassemble
print("\n=== Full disassembly ===")
for ins in dis.get_instructions(target):
    print(f"  {ins.offset:4d} {ins.opname:30s} {ins.argval!r}")

builder = CFGBuilder()
cfg = builder.build(target)

print(f"\n=== CFG blocks: {len(cfg.blocks)} ===")
for b in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
    print(f"\n  Block @ {b.start_offset} (end={b.end_offset}):")
    for ins in b.instructions:
        print(f"    {ins.offset:4d} {ins.opname:30s} {ins.argval!r}")
    print(f"    successors: {[s.start_offset for s in b.successors]}")
    print(f"    predecessors: {[p.start_offset for p in b.predecessors]}")

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

print(f"\n=== Regions: {len(regions)} ===")
for r in regions:
    blocks_sorted = sorted(b.start_offset for b in r.blocks)
    print(f"\n  {type(r).__name__}: blocks={blocks_sorted}")
    if hasattr(r, 'entry') and r.entry:
        print(f"    entry: {r.entry.start_offset}")
    if hasattr(r, 'loop_header') and r.loop_header:
        print(f"    loop_header: {r.loop_header.start_offset}")
    if hasattr(r, 'back_edge_source') and r.back_edge_source:
        print(f"    back_edge_source: {r.back_edge_source.start_offset}")
    if hasattr(r, 'body_blocks') and r.body_blocks:
        print(f"    body_blocks: {sorted(b.start_offset for b in r.body_blocks)}")
    if hasattr(r, 'then_blocks') and r.then_blocks:
        print(f"    then_blocks: {[b.start_offset for b in r.then_blocks]}")
    if hasattr(r, 'else_blocks') and r.else_blocks:
        print(f"    else_blocks: {[b.start_offset for b in r.else_blocks]}")
    if hasattr(r, 'merge_block') and r.merge_block:
        print(f"    merge_block: {r.merge_block.start_offset}")
