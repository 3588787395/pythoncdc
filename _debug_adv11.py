"""Debug adv11_while_walrus_boolop."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

source = """if c:
    while (x := f()) and g():
        pass"""

from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, BoolOpRegion, IfRegion
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.code_generator import CodeGenerator

code = compile(source, '<test>', 'exec')

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)

analyzer = RegionAnalyzer(cfg)
generator = RegionASTGenerator(cfg, analyzer)
result = generator.generate()

code_gen = CodeGenerator()
decompiled = code_gen.generate(result)
print("=== DECOMPILED ===")
print(decompiled)

print("=== REGIONS ===")
for r in analyzer.regions:
    print(f"  {type(r).__name__} blocks={[b.start_offset for b in r.blocks]}")
    if hasattr(r, 'header_block'):
        print(f"    header={r.header_block.start_offset}")
    if hasattr(r, 'body_blocks'):
        print(f"    body_blocks={[b.start_offset for b in r.body_blocks]}")
    if hasattr(r, 'condition_block') and r.condition_block:
        print(f"    condition_block={r.condition_block.start_offset}")

import dis
print("=== BYTECODE ===")
dis.dis(code)
