#!/usr/bin/env python3
"""Debug te026 regression."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from core.cfg.cfg_builder import build_cfg_from_source
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import MatchRegion, TryExceptRegion, LoopRegion, IfRegion
from core.cfg.code_generator import CodeGenerator

src = 'try:\n    for i in range(3):\n        print(i)\nexcept:\n    y = 1'

result = build_cfg_from_source(src)
cfg = result[0] if isinstance(result, (list, tuple)) else result

# Check regions
gen = RegionASTGenerator(cfg)
regions = gen.region_analyzer.analyze()
for r in regions:
    if isinstance(r, TryExceptRegion):
        print(f'TryExceptRegion:')
        print(f'  entry={r.entry.start_offset if r.entry else None}')
        print(f'  try_blocks={[b.start_offset for b in r.try_blocks]}')
        print(f'  blocks={sorted([b.start_offset for b in r.blocks])}')
    elif isinstance(r, LoopRegion):
        print(f'LoopRegion:')
        print(f'  entry={r.entry.start_offset if r.entry else None}')
        print(f'  blocks={sorted([b.start_offset for b in r.blocks])}')

# Check region lookups for try body blocks
try_region = [r for r in regions if isinstance(r, TryExceptRegion)][0]
print(f'\nRegion lookups for try body blocks:')
for block in try_region.try_blocks:
    entry_region = gen.region_analyzer.get_entry_region_for_block(block)
    block_region = gen.region_analyzer.get_region_for_block(block)
    print(f'  try_block {block.start_offset}: entry_region={type(entry_region).__name__ if entry_region else None}, block_region={type(block_region).__name__ if block_region else None}')

# Check the outer region detection
print(f'\nOuter region detection check:')
for block in try_region.try_blocks:
    for r in regions:
        if r is try_region:
            continue
        if isinstance(r, (IfRegion, LoopRegion, TryExceptRegion)):
            if block in r.blocks:
                print(f'  Block {block.start_offset} in {type(r).__name__} (entry={r.entry.start_offset if r.entry else None})')
                print(f'    try_region.entry={try_region.entry.start_offset}')
                print(f'    try_region.entry in r.blocks = {try_region.entry in r.blocks}')
                print(f'    r.entry in try_region.try_blocks = {r.entry in set(try_region.try_blocks)}')

ast_result = gen.generate()
source = CodeGenerator().generate(ast_result)
print(f'\nDECOMPILED:\n{source}')
