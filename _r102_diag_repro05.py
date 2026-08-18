#!/usr/bin/env python3
"""诊断脚本：查看repro_05的区域分析结果"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, IfRegion

pyc_path = os.path.join('.trae', 'specs', 'decompiler-test-comprehensive-10rounds', 'rounds', 'round_01', 'test_engineer', 'minimal_repros', 'repro_05_try_else_finally_return.pyc')

import marshal
import types

with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

# Find the target function
target_func = None
for const in code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'integration_test':
        target_func = const
        break

if target_func is None:
    print("Function integration_test not found!")
    sys.exit(1)

cfg = build_cfg(target_func)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print(f"Total regions: {len(analyzer.regions)}")
for r in analyzer.regions:
    cls = type(r).__name__
    entry_off = r.entry.start_offset if r.entry is not None else None
    if isinstance(r, TryExceptRegion):
        print(f"\n[{cls}] entry={entry_off}")
        print(f"  try_range=({r.try_offset_start},{r.try_offset_end})")
        print(f"  try_blocks={[b.start_offset for b in r.try_blocks]}")
        print(f"  handler_entry_blocks={[b.start_offset for b in r.handler_entry_blocks]}")
        print(f"  except_handlers ({len(r.except_handlers)}):")
        for i, (exc_type, exc_name, hblocks) in enumerate(r.except_handlers):
            print(f"    [{i}] exc_type={exc_type!r} exc_name={exc_name!r} blocks={[b.start_offset for b in hblocks]}")
        print(f"  else_blocks={[b.start_offset for b in r.else_blocks]}")
        print(f"  finally_blocks={[b.start_offset for b in r.finally_blocks]}")
        print(f"  cleanup_blocks={[b.start_offset for b in r.cleanup_blocks]}")
        print(f"  has_else={r.has_else} has_finally={r.has_finally}")
        print(f"  all blocks={[b.start_offset for b in r.blocks]}")
    else:
        print(f"\n[{cls}] entry={entry_off} blocks={sorted(b.start_offset for b in r.blocks)}")

print("\n\n=== Block to Region mapping ===")
for block in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
    region = analyzer.block_to_region.get(block)
    if region:
        cls = type(region).__name__
        print(f"  block {block.start_offset} -> {cls} (entry={region.entry.start_offset if region.entry else None})")

# Also print CFG
print("\n=== CFG Blocks ===")
for block in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
    instrs = [(i.opname, i.argval) for i in block.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG')]
    succs = [s.start_offset for s in block.successors]
    print(f"  block {block.start_offset}: instrs={instrs} succs={succs}")
