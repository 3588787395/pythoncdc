#!/usr/bin/env python3
"""R12 debug: trace CFG + region identification for repro_01 (Pattern A2)."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(PROJECT_ROOT))

import py_compile
import marshal
from pycdc import decompile_pyc
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.cfg_builder import CFGBuilder

REPRO = PROJECT_ROOT / '.trae/specs/region-comment-multi-pyc-iteration/rounds/round_12/test_engineer/minimal_repros/repro_01_try_if_else_return.py'

# Compile
pyc_path = REPRO.with_suffix('.pyc')
py_compile.compile(str(REPRO), cfile=str(pyc_path), doraise=True)

# Load code
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

# Find the f function code object
f_code = None
for const in code.co_consts:
    if hasattr(const, 'co_name') and const.co_name == 'f':
        f_code = const
        break

print(f'f_code: {f_code}')
print(f'co_consts: {f_code.co_consts}')

# Build CFG
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(f_code)

print('\n=== BLOCKS ===')
for block in cfg.get_blocks_in_order():
    print(f'\nBlock @ {block.start_offset}:')
    for instr in block.instructions:
        print(f'  {instr.offset:4d} {instr.opname:30s} {instr.argval}')
    print(f'  successors: {[s.start_offset for s in block.successors]}')
    print(f'  cond_successors: {[s.start_offset for s in block.conditional_successors]}')
    print(f'  exception_successors: {[s.start_offset for s in getattr(block, "exception_successors", [])]}')

# Analyze regions
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print('\n=== REGIONS ===')
for region in analyzer.regions:
    print(f'{type(region).__name__} entry={region.entry.start_offset} blocks={[b.start_offset for b in region.blocks]}')
    if hasattr(region, 'try_blocks'):
        print(f'  try_blocks={[b.start_offset for b in region.try_blocks]}')
    if hasattr(region, 'handler_blocks'):
        print(f'  handler_blocks={[b.start_offset for b in region.handler_blocks]}')
    if hasattr(region, 'then_blocks'):
        print(f'  then_blocks={[b.start_offset for b in region.then_blocks]}')
    if hasattr(region, 'else_blocks'):
        print(f'  else_blocks={[b.start_offset for b in region.else_blocks]}')

print('\n=== block_to_region ===')
for block in cfg.get_blocks_in_order():
    r = analyzer.block_to_region.get(block)
    print(f'  block {block.start_offset} -> {type(r).__name__ if r else None}')
