#!/usr/bin/env python3
"""Diagnose async function body drop: show CFG regions for repro_10."""
import sys, os, types, marshal, dis
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

REPRO_DIR = PROJECT_ROOT / '.trae' / 'specs' / 'region-comprehensive-pyc-10rounds' / 'rounds' / 'round_01' / 'test_engineer' / 'minimal_repros'

pyc_path = REPRO_DIR / 'repro_10_as1_async_await_body.pyc'

with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

# Find the 'test' function code object
for const in code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'test':
        test_code = const
        break

print("=" * 70)
print("ASYNC FUNCTION: test()")
print("=" * 70)
print(f"co_name: {test_code.co_name}")
print(f"co_flags: {test_code.co_flags} (CO_COROUTINE={0x100})")
print(f"Is coroutine: {bool(test_code.co_flags & 0x100)}")
print(f"co_varnames: {test_code.co_varnames}")
print(f"co_consts: {test_code.co_consts}")
print()

print("--- ORIGINAL BYTECODE ---")
dis.dis(test_code)
print()

# Build CFG
cfg = build_cfg(test_code)
print(f"--- CFG BLOCKS ({len(cfg.blocks)} blocks) ---")
for offset, block in sorted(cfg.blocks.items()):
    instrs = [(i.opname, i.argval) for i in block.instructions]
    succs = [s.start_offset for s in block.successors]
    preds = [p.start_offset for p in block.predecessors]
    print(f"  Block {offset}: instrs={instrs}")
    print(f"    succs={succs}, preds={preds}")

# Analyze regions
print(f"\n--- REGION ANALYSIS ---")
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
for r in regions:
    print(f"  Region: type={r.region_type}, entry={r.entry.start_offset if r.entry else None}")
    print(f"    blocks={[b.start_offset for b in r.blocks]}")
    if hasattr(r, 'else_blocks') and r.else_blocks:
        print(f"    else_blocks={[b.start_offset for b in r.else_blocks]}")
    if hasattr(r, 'body_blocks') and r.body_blocks:
        print(f"    body_blocks={[b.start_offset for b in r.body_blocks]}")
    if hasattr(r, 'header_block') and r.header_block:
        print(f"    header_block={r.header_block.start_offset}")
    if hasattr(r, 'condition_block') and r.condition_block:
        print(f"    condition_block={r.condition_block.start_offset}")

print(f"\n--- block_to_region mapping ---")
for block_offset, region in sorted(analyzer.block_to_region.items()):
    print(f"  Block {block_offset} -> Region type={region.region_type}, entry={region.entry.start_offset if region.entry else None}")
