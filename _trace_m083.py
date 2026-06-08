#!/usr/bin/env python3
"""Deep trace for m083 guard issue."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from core.cfg.cfg_builder import build_cfg_from_source
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

# Patch _collect_guard_pattern_blocks to trace
_orig_collect = RegionASTGenerator._collect_guard_pattern_blocks
def _traced_collect(self, region, case_idx):
    guard = region.case_guards[case_idx] if case_idx < len(region.case_guards) else None
    print(f'  [_collect_guard_pattern_blocks] case_idx={case_idx}, guard={guard}')
    result = _orig_collect(self, region, case_idx)
    print(f'  [_collect_guard_pattern_blocks] result={[b.start_offset for b in result]}')
    return result

RegionASTGenerator._collect_guard_pattern_blocks = _traced_collect

def decompile(src, name):
    print(f'\n{"="*70}')
    print(f'TEST: {name}')
    print(f'{"="*70}')
    result = build_cfg_from_source(src)
    cfg = result[0] if isinstance(result, (list, tuple)) else result
    gen = RegionASTGenerator(cfg)
    ast_result = gen.generate()
    source = CodeGenerator().generate(ast_result)
    print(f'\nDECOMPILED:\n{source}')

decompile('''match value:
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
''', 'm083')
