"""Debug bool19_ternary_combo: analyze CFG blocks and regions"""
import sys
sys.path.insert(0, '/workspace')

import dis
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

SOURCE = "result = (a and b) or (c and d) or None"

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
    if hasattr(region, 'value_target') and region.value_target:
        print(f"  value_target: {region.value_target}")
    if hasattr(region, 'prefix_block') and region.prefix_block:
        print(f"  prefix_block: {region.prefix_block.id}")
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
print("\n--- recompiled bytecode ---")
recompiled = compile(output, '<decompiled>', 'exec')
dis.dis(recompiled)
