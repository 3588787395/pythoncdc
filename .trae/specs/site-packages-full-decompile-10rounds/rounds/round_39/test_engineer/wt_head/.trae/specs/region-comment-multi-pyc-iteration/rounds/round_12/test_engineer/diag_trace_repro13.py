#!/usr/bin/env python3
"""R12 debug: trace CFG + regions for repro_13 (ternary assign + return in try)."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(PROJECT_ROOT))

import py_compile
import marshal
from core.cfg.region_analyzer import RegionAnalyzer, TernaryRegion, IfRegion, TryExceptRegion
from core.cfg.cfg_builder import CFGBuilder

REPRO = PROJECT_ROOT / '.trae/specs/region-comment-multi-pyc-iteration/rounds/round_12/test_engineer/minimal_repros/repro_13_try_if_ternary_assign_return.py'

pyc_path = REPRO.with_suffix('.pyc')
py_compile.compile(str(REPRO), cfile=str(pyc_path), doraise=True)

with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

f_code = None
for const in code.co_consts:
    if hasattr(const, 'co_name') and const.co_name == 'f':
        f_code = const
        break

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(f_code)

print('=== BLOCKS ===')
for block in cfg.get_blocks_in_order():
    print(f'\nBlock @ {block.start_offset}:')
    for instr in block.instructions:
        print(f'  {instr.offset:4d} {instr.opname:30s} {instr.argval}')
    print(f'  successors: {[s.start_offset for s in block.successors]}')
    print(f'  cond_successors: {[s.start_offset for s in block.conditional_successors]}')
    _exc = getattr(block, 'exception_successors', set())
    print(f'  exception_successors: {[s.start_offset for s in _exc]}')

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print('\n=== REGIONS ===')
for region in analyzer.regions:
    print(f'{type(region).__name__} entry={region.entry.start_offset} blocks={sorted(b.start_offset for b in region.blocks)}')
    if hasattr(region, 'try_blocks'):
        print(f'  try_blocks={sorted(b.start_offset for b in region.try_blocks)}')
    if hasattr(region, 'then_blocks'):
        print(f'  then_blocks={sorted(b.start_offset for b in region.then_blocks)}')
    if hasattr(region, 'else_blocks'):
        print(f'  else_blocks={sorted(b.start_offset for b in region.else_blocks)}')
    if hasattr(region, 'merge_block') and region.merge_block:
        print(f'  merge_block={region.merge_block.start_offset}')

print('\n=== block_to_region ===')
for block in cfg.get_blocks_in_order():
    r = analyzer.block_to_region.get(block)
    print(f'  block {block.start_offset} -> {type(r).__name__ if r else None}')
