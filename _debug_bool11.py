"""Debug bool11_in_while: analyze CFG blocks and regions"""
import sys
sys.path.insert(0, '/workspace')

import dis
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

SOURCE = "while not done and has_data():\n    process()"

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
for bid, block in cfg.blocks.items():
    print(f"\n# block id={block.id} (start_offset={block.start_offset}):")
    for instr in block.instructions:
        print(f"  {instr.offset:4d} {instr.opname:30s} arg={instr.arg!r} argval={instr.argval!r}")
    print(f"  successors: {[s.id for s in block.successors]}")
    print(f"  predecessors: {[p.id for p in block.predecessors]}")

print("\n" + "=" * 80)
print("REGIONS:")
print("=" * 80)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

for region in regions:
    print(f"\n{region.region_type}: blocks={[b.id for b in region.blocks]}")
    if hasattr(region, 'op_chain'):
        print(f"  op_chain: {[(b.id, op) for b, op in region.op_chain]}")
    if hasattr(region, 'merge_block') and region.merge_block:
        print(f"  merge_block: {region.merge_block.id}")
    if hasattr(region, 'header_block') and region.header_block:
        print(f"  header_block: {region.header_block.id}")
    if hasattr(region, 'body_blocks'):
        print(f"  body_blocks: {[b.id for b in region.body_blocks]}")
    if hasattr(region, 'else_blocks'):
        print(f"  else_blocks: {[b.id for b in region.else_blocks]}")
    if hasattr(region, 'then_blocks'):
        print(f"  then_blocks: {[b.id for b in region.then_blocks]}")
    if hasattr(region, 'condition_block') and region.condition_block:
        print(f"  condition_block: {region.condition_block.id}")
    if hasattr(region, 'back_edge_block') and region.back_edge_block:
        print(f"  back_edge_block: {region.back_edge_block.id}")
    if hasattr(region, 'back_edge_blocks') and region.back_edge_blocks:
        print(f"  back_edge_blocks: {[b.id for b in region.back_edge_blocks]}")
    if hasattr(region, 'condition_recheck_blocks') and region.condition_recheck_blocks:
        print(f"  condition_recheck_blocks: {[b.id for b in region.condition_recheck_blocks]}")
    if hasattr(region, 'condition_chain_blocks') and region.condition_chain_blocks:
        print(f"  condition_chain_blocks: {[b.id for b in region.condition_chain_blocks]}")
    if hasattr(region, 'pre_condition_blocks') and region.pre_condition_blocks:
        print(f"  pre_condition_blocks: {[b.id for b in region.pre_condition_blocks]}")
    if hasattr(region, 'break_blocks') and region.break_blocks:
        print(f"  break_blocks: {[b.id for b in region.break_blocks]}")
    if hasattr(region, 'condition_expr'):
        print(f"  condition_expr: {region.condition_expr}")
    if hasattr(region, 'value_target') and region.value_target:
        print(f"  value_target: {region.value_target}")

print("\n" + "=" * 80)
print("DECOMPILED:")
print("=" * 80)
generator = RegionASTGenerator(cfg, analyzer)
result = generator.generate()
code_gen = CodeGenerator()
output = code_gen.generate(result)
print(output)
print("\n--- recompiled bytecode ---")
recompiled = compile(output, '<decompiled>', 'exec')
dis.dis(recompiled)
