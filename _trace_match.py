#!/usr/bin/env python3
"""Focused debug for match+try failures - trace the exact code path."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from core.cfg.cfg_builder import build_cfg_from_source
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

# Patch _generate_try_body to trace execution
_orig_generate_try_body = RegionASTGenerator._generate_try_body
def _traced_generate_try_body(self, region):
    print(f'  [_generate_try_body] entry={region.entry.start_offset if region.entry else None}')
    print(f'  [_generate_try_body] try_blocks={[b.start_offset for b in region.try_blocks]}')
    print(f'  [_generate_try_body] generated_blocks={sorted(b.start_offset for b in self.generated_blocks)}')
    for block in sorted(region.try_blocks, key=lambda b: b.start_offset):
        print(f'  [_generate_try_body] Processing try_block {block.start_offset}: {[(i.opname, i.argval) for i in block.instructions]}')
        if block in self.generated_blocks:
            print(f'    -> ALREADY IN generated_blocks, SKIPPED')
    result = _orig_generate_try_body(self, region)
    print(f'  [_generate_try_body] result={result}')
    return result

RegionASTGenerator._generate_try_body = _traced_generate_try_body

# Patch _generate_match to trace execution
_orig_generate_match = RegionASTGenerator._generate_match
def _traced_generate_match(self, region):
    print(f'[_generate_match] subject_block={region.subject_block.start_offset if region.subject_block else None}')
    print(f'[_generate_match] case_patterns={region.case_patterns}')
    print(f'[_generate_match] case_bodies={[[b.start_offset for b in body] for body in region.case_bodies]}')
    print(f'[_generate_match] case_body_start_indices={region.case_body_start_indices}')
    print(f'[_generate_match] generated_blocks at start={sorted(b.start_offset for b in self.generated_blocks)}')
    result = _orig_generate_match(self, region)
    print(f'[_generate_match] result type={result.get("type") if isinstance(result, dict) else type(result).__name__}')
    if isinstance(result, dict) and result.get('type') == 'Match':
        for i, case in enumerate(result.get('cases', [])):
            print(f'  case {i}: pattern={case.get("pattern")}, guard={case.get("guard")}, body={case.get("body")}')
    return result

RegionASTGenerator._generate_match = _traced_generate_match

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

# Focus on m054 first
decompile('match x:\n    case 1:\n        try:\n            y = 1\n        except:\n            z = 2\n    case _:\n        pass', 'm054')
