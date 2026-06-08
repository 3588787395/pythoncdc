#!/usr/bin/env python3
"""Debug te026 - trace _generate_try_body for block 4."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from core.cfg.cfg_builder import build_cfg_from_source
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import TryExceptRegion, LoopRegion
from core.cfg.code_generator import CodeGenerator

# Patch _generate_try_body to trace
_orig = RegionASTGenerator._generate_try_body
def _traced(self, region):
    print(f'[_generate_try_body] entry={region.entry.start_offset}, try_blocks={[b.start_offset for b in region.try_blocks]}')
    print(f'[_generate_try_body] generated_blocks at start={sorted(b.start_offset for b in self.generated_blocks)}')
    result = _orig(self, region)
    print(f'[_generate_try_body] result={result}')
    return result
RegionASTGenerator._generate_try_body = _traced

# Patch _generate_block_statements to trace
_orig2 = RegionASTGenerator._generate_block_statements
def _traced2(self, block):
    result = _orig2(self, block)
    if result:
        print(f'  [_generate_block_statements] block={block.start_offset}, result={result}')
    return result
RegionASTGenerator._generate_block_statements = _traced2

src = 'try:\n    for i in range(3):\n        print(i)\nexcept:\n    y = 1'
result = build_cfg_from_source(src)
cfg = result[0] if isinstance(result, (list, tuple)) else result
gen = RegionASTGenerator(cfg)
ast_result = gen.generate()
source = CodeGenerator().generate(ast_result)
print(f'\nDECOMPILED:\n{source}')
