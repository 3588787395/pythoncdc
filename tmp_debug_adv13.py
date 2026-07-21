"""Debug script for adv13: if (a if c else b) or (d if e else f) or (g if h else i): pass"""
import sys
import os
import dis
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, RegionType, BoolOpRegion, IfRegion, TernaryRegion
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator


SOURCE = """if (a if c else b) or (d if e else f) or (g if h else i):
    pass"""

code = compile(SOURCE, '<test>', 'exec')
print("=== Original bytecode ===")
dis.dis(code)
print()

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print("=== Regions detected ===")
for r in analyzer.regions:
    print(f"  {type(r).__name__}: entry={r.entry.start_offset}, blocks={sorted(b.start_offset for b in r.blocks)}")
    if isinstance(r, BoolOpRegion):
        print(f"    op_chain: {[(b.start_offset, op) for b, op in r.op_chain]}")
        print(f"    merge_block: {r.merge_block.start_offset if r.merge_block else None}")
        print(f"    is_condition_context: {getattr(r, 'is_condition_context', None)}")
        print(f"    value_target: {r.value_target}")

print()
print("=== Block -> Region ===")
for offset in sorted(cfg.blocks.keys()):
    b = cfg.blocks[offset]
    r = analyzer.block_to_region.get(b)
    print(f"  block {offset}: region = {type(r).__name__ if r else None}")

print()
print("=== Generated AST ===")
generator = RegionASTGenerator(cfg, analyzer)
result = generator.generate()
code_gen = CodeGenerator()
output = code_gen.generate(result)
print(output)
print()
print("=== Recompiled bytecode ===")
recompiled = compile(output, '<decompiled>', 'exec')
dis.dis(recompiled)
