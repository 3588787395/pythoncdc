#!/usr/bin/env python3
"""Deep analysis of m075 - BoolOp in match case body."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from core.cfg.cfg_builder import build_cfg_from_source
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, MatchRegion, IfRegion, BoolOpRegion
from core.cfg.code_generator import CodeGenerator

src = 'match x:\n    case 1:\n        if a and b:\n            y = 1\n        elif a or c:\n            y = 2\n        else:\n            y = 3\n    case _:\n        y = 0'

print(f'SOURCE:\n{src}')

result = build_cfg_from_source(src)
cfg = result[0] if isinstance(result, (list, tuple)) else result

# Show blocks
print(f'\nCFG blocks:')
for block in cfg.get_blocks_in_order():
    instrs = [(i.opname, i.argval) for i in block.instructions]
    print(f'  Block {block.start_offset}: {instrs}')
    succs = [s.start_offset for s in block.successors]
    preds = [p.start_offset for p in block.predecessors]
    print(f'    succs={succs}, preds={preds}')

# Show regions
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
print(f'\nRegions ({len(regions)}):')
for r in regions:
    if isinstance(r, MatchRegion):
        print(f'  MatchRegion:')
        print(f'    subject_block: {r.subject_block.start_offset if r.subject_block else None}')
        print(f'    case_patterns: {r.case_patterns}')
        print(f'    case_guards: {r.case_guards}')
        print(f'    case_bodies: {[[b.start_offset for b in body] for body in r.case_bodies]}')
        print(f'    case_body_start_indices: {r.case_body_start_indices}')
        print(f'    blocks: {sorted([b.start_offset for b in r.blocks])}')
        print(f'    parent: {type(r.parent).__name__ if r.parent else None}')
    elif isinstance(r, IfRegion):
        print(f'  IfRegion:')
        print(f'    entry: {r.entry.start_offset if r.entry else None}')
        print(f'    condition_block: {r.condition_block.start_offset if hasattr(r, "condition_block") and r.condition_block else None}')
        print(f'    blocks: {sorted([b.start_offset for b in r.blocks])}')
        print(f'    parent: {type(r.parent).__name__ if r.parent else None}')
    elif isinstance(r, BoolOpRegion):
        print(f'  BoolOpRegion:')
        print(f'    entry: {r.entry.start_offset if r.entry else None}')
        print(f'    blocks: {sorted([b.start_offset for b in r.blocks])}')
        print(f'    parent: {type(r.parent).__name__ if r.parent else None}')
    else:
        print(f'  {type(r).__name__}: blocks={sorted([b.start_offset for b in r.blocks])}')

# Check what get_entry_region_for_block returns for each block in the case body
print(f'\nRegion lookups for case body blocks:')
gen = RegionASTGenerator(cfg)
for block in cfg.get_blocks_in_order():
    entry_region = gen.region_analyzer.get_entry_region_for_block(block)
    block_region = gen.region_analyzer.get_region_for_block(block)
    print(f'  Block {block.start_offset}: entry_region={type(entry_region).__name__ if entry_region else None}, block_region={type(block_region).__name__ if block_region else None}')

# Decompile
gen2 = RegionASTGenerator(cfg)
ast_result = gen2.generate()
source = CodeGenerator().generate(ast_result)
print(f'\nDECOMPILED:\n{source}')
