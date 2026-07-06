#!/usr/bin/env python3
"""Debug m071 regression."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from core.cfg.cfg_builder import build_cfg_from_source
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import MatchRegion, LoopRegion, IfRegion
from core.cfg.code_generator import CodeGenerator

src = 'match x:\n    case 1:\n        for i in range(3):\n            for j in range(3):\n                y = i + j\n    case _:\n        y = 0'

result = build_cfg_from_source(src)
cfg = result[0] if isinstance(result, (list, tuple)) else result

# Patch _generate_match to trace execution
_orig_generate_match = RegionASTGenerator._generate_match
def _traced_generate_match(self, region):
    print(f'[_generate_match] START')
    print(f'  subject_block={region.subject_block.start_offset if region.subject_block else None}')
    print(f'  case_patterns={region.case_patterns}')
    print(f'  case_bodies={[[b.start_offset for b in body] for body in region.case_bodies]}')
    print(f'  generated_blocks at start={sorted(b.start_offset for b in self.generated_blocks)}')
    result = _orig_generate_match(self, region)
    print(f'[_generate_match] END, result type={result.get("type") if isinstance(result, dict) else type(result).__name__}')
    return result

RegionASTGenerator._generate_match = _traced_generate_match

# Patch _try_generate_if_chain_in_match_body to trace
_orig_try_if_chain = RegionASTGenerator._try_generate_if_chain_in_match_body
def _traced_try_if_chain(self, body_blocks, region):
    print(f'[_try_generate_if_chain] called with body_blocks={[b.start_offset for b in body_blocks]}')
    result, consumed = _orig_try_if_chain(self, body_blocks, region)
    print(f'[_try_generate_if_chain] result={type(result).__name__ if result else None}, consumed={[b.start_offset for b in consumed]}')
    return result, consumed

RegionASTGenerator._try_generate_if_chain_in_match_body = _traced_try_if_chain

gen = RegionASTGenerator(cfg)
ast_result = gen.generate()
source = CodeGenerator().generate(ast_result)
print(f'\nDECOMPILED:\n{source}')
