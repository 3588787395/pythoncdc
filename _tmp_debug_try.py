#!/usr/bin/env python3
"""Debug TryExceptRegion identification for exception_handling_examples"""
import sys, marshal
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, IfRegion, LoopRegion

def load_pyc_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.loads(f.read())

orig_code = load_pyc_code('python_syntax_comprehensive_test.pyc')
for c in orig_code.co_consts:
    if hasattr(c, 'co_code') and c.co_name == 'exception_handling_examples':
        func_code = c
        break

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(func_code)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

blocks = list(cfg.blocks.values())
print("=== Blocks 280-400 ===")
for block in sorted(blocks, key=lambda b: b.start_offset):
    if 280 <= block.start_offset <= 400:
        succs = [s.start_offset for s in block.successors]
        preds = [p.start_offset for p in block.predecessors]
        region = analyzer.get_region_for_block(block)
        rinfo = type(region).__name__ + f"@{region.entry.start_offset}" if region else "None"
        print(f"  @{block.start_offset}: preds={preds} succs={succs} region={rinfo}")
        for i in block.instructions:
            print(f"    {i.offset:4d}: {i.opname:30s} {i.argval}")

print("\n=== TryExceptRegions ===")
for r in analyzer.regions:
    if isinstance(r, TryExceptRegion):
        print(f"  TryExceptRegion@{r.entry.start_offset}:")
        print(f"    try_blocks: {[b.start_offset for b in r.try_blocks]}")
        print(f"    handler_blocks: {[h.start_offset for h in r.handler_blocks] if r.handler_blocks else 'None'}")
        print(f"    else_blocks: {[b.start_offset for b in r.else_blocks] if r.else_blocks else 'None'}")
        print(f"    finally_blocks: {[b.start_offset for b in r.finally_blocks] if r.finally_blocks else 'None'}")
        if hasattr(r, 'merge_block') and r.merge_block:
            print(f"    merge_block: {r.merge_block.start_offset}")
        print(f"    has_else: {r.has_else}")
        print(f"    has_finally: {r.has_finally}")
