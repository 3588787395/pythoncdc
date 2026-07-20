"""Debug bool20_complex_logic: analyze CFG blocks and regions"""
import sys
import os
sys.path.insert(0, '/workspace')

import dis
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

SOURCE = "if (user and user.is_active() and (user.has_permission('read') or user.is_admin()) and resource.exists()):\n    access(resource)"

code = compile(SOURCE, '<test>', 'exec')

print("=" * 80)
print("ORIGINAL BYTECODE:")
print("=" * 80)
dis.dis(code)

print("\n" + "=" * 80)
print("CFG BLOCKS:")
print("=" * 80)
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)
print(f"block_count: {len(cfg.blocks)}")
for bid in cfg.blocks:
    block = cfg.get_block(bid)
    print(f"\n@{block.offset} (id={block.id}):")
    for instr in block.instructions:
        print(f"  {instr.offset:4d} {instr.opname:30s} arg={instr.arg!r} argval={instr.argval!r}")
    print(f"  successors: {[b for b in block.successors]}")
    print(f"  predecessors: {[b for b in block.predecessors]}")

print("\n" + "=" * 80)
print("REGIONS:")
print("=" * 80)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

for region in regions:
    print(f"\n{region.region_type}: blocks={region.blocks}")
    print(f"  entry_block: {region.entry_block.offset if region.entry_block else None}")
    if hasattr(region, 'op_chain'):
        print(f"  op_chain: {[(b.offset, op) for b, op in region.op_chain]}")
    if hasattr(region, 'merge_block') and region.merge_block:
        print(f"  merge_block: {region.merge_block.offset}")
    if hasattr(region, 'then_blocks'):
        print(f"  then_blocks: {[b.offset for b in region.then_blocks]}")
    if hasattr(region, 'else_blocks'):
        print(f"  else_blocks: {[b.offset for b in region.else_blocks]}")
    if hasattr(region, 'condition_block') and region.condition_block:
        print(f"  condition_block: {region.condition_block.offset}")
    if hasattr(region, 'condition_expr'):
        print(f"  condition_expr: {region.condition_expr}")

print("\n" + "=" * 80)
print("DECOMPILED:")
print("=" * 80)
generator = RegionASTGenerator(cfg, analyzer)
result = generator.generate()
code_gen = CodeGenerator()
output = code_gen.generate(result)
print(output)
