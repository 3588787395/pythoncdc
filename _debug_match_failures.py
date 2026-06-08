#!/usr/bin/env python3
"""Debug match_region failures - show CFG, regions, and detailed decompilation info."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from core.cfg.cfg_builder import build_cfg_from_source
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, MatchRegion, TryExceptRegion, IfRegion, BoolOpRegion
from core.cfg.code_generator import CodeGenerator

def debug_decompile(src, name):
    print(f'\n{"="*70}')
    print(f'TEST: {name}')
    print(f'{"="*70}')
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
    gen = RegionASTGenerator(cfg)
    regions = gen.region_analyzer.analyze()
    print(f'\nRegions ({len(regions)}):')
    for r in regions:
        if isinstance(r, MatchRegion):
            print(f'  MatchRegion:')
            print(f'    subject_block: {r.subject_block.start_offset if r.subject_block else None}')
            print(f'    case_patterns: {r.case_patterns}')
            print(f'    case_guards: {r.case_guards}')
            print(f'    case_bodies: {[[b.start_offset for b in body] for body in r.case_bodies]}')
            print(f'    case_body_start_indices: {r.case_body_start_indices}')
            print(f'    merge_block: {r.merge_block.start_offset if r.merge_block else None}')
            print(f'    blocks: {sorted([b.start_offset for b in r.blocks])}')
        elif isinstance(r, TryExceptRegion):
            print(f'  TryExceptRegion:')
            print(f'    entry: {r.entry.start_offset if r.entry else None}')
            print(f'    condition_block: {r.condition_block.start_offset if hasattr(r, "condition_block") and r.condition_block else None}')
            try:
                print(f'    try_blocks: {[b.start_offset for b in r.try_blocks] if hasattr(r, "try_blocks") else "N/A"}')
            except:
                print(f'    try_blocks: N/A')
            try:
                print(f'    handler_blocks: {[b.start_offset for b in r.handler_blocks] if hasattr(r, "handler_blocks") else "N/A"}')
            except:
                print(f'    handler_blocks: N/A')
            print(f'    blocks: {sorted([b.start_offset for b in r.blocks])}')
            # Show more details
            for attr in ['try_body', 'handlers', 'else_body', 'finally_body']:
                if hasattr(r, attr):
                    val = getattr(r, attr)
                    if val:
                        if isinstance(val, list):
                            if val and hasattr(val[0], 'start_offset'):
                                print(f'    {attr}: {[b.start_offset for b in val]}')
                            else:
                                print(f'    {attr}: {val}')
                        elif hasattr(val, 'start_offset'):
                            print(f'    {attr}: {val.start_offset}')
                        else:
                            print(f'    {attr}: {val}')
        elif isinstance(r, IfRegion):
            print(f'  IfRegion:')
            print(f'    entry: {r.entry.start_offset if r.entry else None}')
            print(f'    condition_block: {r.condition_block.start_offset if hasattr(r, "condition_block") and r.condition_block else None}')
            print(f'    blocks: {sorted([b.start_offset for b in r.blocks])}')
        elif isinstance(r, BoolOpRegion):
            print(f'  BoolOpRegion:')
            print(f'    entry: {r.entry.start_offset if r.entry else None}')
            print(f'    blocks: {sorted([b.start_offset for b in r.blocks])}')
        else:
            print(f'  {type(r).__name__}: blocks={sorted([b.start_offset for b in r.blocks])}')
    
    # Generate AST
    ast_result = gen.generate()
    source = CodeGenerator().generate(ast_result)
    print(f'\nDECOMPILED:\n{source}')

# Test cases (actual test file source codes)
tests = {
    'm054': 'match x:\n    case 1:\n        try:\n            y = 1\n        except:\n            z = 2\n    case _:\n        pass',
    'm061': 'match x:\n    case 1:\n        try:\n            y = risky()\n        except:\n            y = 0\n    case _:\n        y = -1',
    'm069': 'match x:\n    case 1:\n        try:\n            x = risky()\n        except ValueError:\n            x = 0\n        except TypeError:\n            x = -1\n    case _:\n        x = 0',
    'm075': 'match x:\n    case 1:\n        if a and b:\n            y = 1\n        elif a or c:\n            y = 2\n        else:\n            y = 3\n    case _:\n        y = 0',
    'm083': '''match value:
    case int() as n if n > 0:
        result = f'positive integer: {n}'
    case int() as n if n < 0:
        result = f'negative integer: {n}'
    case str() as s if s:
        result = f'non-empty string: {s}'
    case list() as lst if len(lst) > 0:
        result = f'non-empty list: {len(lst)} items'
    case _:
        result = 'other'
''',
}

for name, src in tests.items():
    try:
        debug_decompile(src, name)
    except Exception as e:
        print(f'ERROR: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()
