#!/usr/bin/env python3
"""R100: Analyze region identification for check_strategy"""
import sys, marshal, types
sys.path.insert(0, '.')

pyc_path = 'site-packages/IQCommon/api/check_strategy.pyc'
code = marshal.loads(open(pyc_path, 'rb').read()[16:])
funcs = [c for c in code.co_consts if isinstance(c, types.CodeType)]
cs = [f for f in funcs if f.co_name == 'check_strategy'][0]

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

builder = CFGBuilder()
cfg = builder.build(cs)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

print('=== Regions identified ===')
for r in regions:
    print(f'  Region type={r.region_type.name}, entry={r.entry.start_offset if r.entry else None}')
    if hasattr(r, 'chained_compare_ops'):
        print(f'    chained_compare_ops={r.chained_compare_ops}')
    if hasattr(r, 'chained_compare_blocks'):
        print(f'    chained_compare_blocks={[b.start_offset for b in r.chained_compare_blocks]}')
    if hasattr(r, 'then_blocks'):
        print(f'    then_blocks={[b.start_offset for b in r.then_blocks]}')
    if hasattr(r, 'else_blocks'):
        print(f'    else_blocks={[b.start_offset for b in r.else_blocks]}')
    if hasattr(r, 'condition_block'):
        print(f'    condition_block={r.condition_block.start_offset if r.condition_block else None}')
    print(f'    blocks={[b.start_offset for b in r.blocks]}')

print('\n=== block_to_region ===')
for block in cfg.get_blocks_in_order():
    owner = analyzer.block_to_region.get(block)
    if owner:
        print(f'  Block @ {block.start_offset:4d} -> {owner.region_type.name} (entry={owner.entry.start_offset if owner.entry else None})')
