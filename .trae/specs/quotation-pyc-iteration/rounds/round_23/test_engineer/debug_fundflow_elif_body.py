"""R23-N8 调试 get_fundflow_day 的 elif body 生成过程"""
import sys
import types
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, MatchRegion, IfRegion, LoopRegion, RegionType
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

target = None
for const in code_obj.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'get_fundflow_day':
        target = const
        break

print(f"Found: {target.co_name}")

builder = CFGBuilder()
cfg = builder.build(target)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find the IF_ELIF_CHAIN region at block 70
target_region = None
for region in analyzer.regions:
    if isinstance(region, IfRegion) and region.entry and region.entry.start_offset == 70:
        target_region = region
        break

print(f"\nTarget region: {type(target_region).__name__}, type={target_region.region_type}")
print(f"  blocks: {[b.start_offset for b in target_region.blocks]}")
print(f"  then_blocks: {[b.start_offset for b in target_region.then_blocks]}")
print(f"  elif_conditions: {[b.start_offset for b in target_region.elif_conditions]}")
print(f"  elif_bodies: {[[b.start_offset for b in body] for body in target_region.elif_bodies]}")
print(f"  elif_final_else: {[b.start_offset for b in target_region.elif_final_else]}")
print(f"  children: {[(type(c).__name__, c.entry.start_offset if c.entry else None) for c in getattr(target_region, 'children', [])]}")

# Test get_entry_region_for_block for each block in elif_bodies[0]
elif_body = target_region.elif_bodies[0]
print(f"\n=== elif_body[0] blocks: {[b.start_offset for b in elif_body]} ===")
for b in elif_body:
    entry_region = analyzer.get_entry_region_for_block(b)
    region_for = analyzer.get_region_for_block(b)
    print(f"  Block@{b.start_offset}: entry_region={type(entry_region).__name__ if entry_region else None} (entry={entry_region.entry.start_offset if entry_region and entry_region.entry else None}), region_for={type(region_for).__name__ if region_for else None}")

# Check LoopRegion metadata
print(f"\n=== LoopRegion metadata ===")
for region in analyzer.regions:
    if isinstance(region, LoopRegion):
        print(f"  LoopRegion entry={region.entry.start_offset if region.entry else None}")
        print(f"    blocks: {[b.start_offset for b in region.blocks]}")
        print(f"    header_block: {region.header_block.start_offset if region.header_block else None}")
        print(f"    body_blocks: {[b.start_offset for b in region.body_blocks] if region.body_blocks else None}")
        print(f"    condition_block: {region.condition_block.start_offset if region.condition_block else None}")
        fis = region.metadata.get('for_iter_setup')
        print(f"    for_iter_setup: {fis.start_offset if fis else None}")
        print(f"    metadata keys: {list(region.metadata.keys())}")

# Now generate AST and trace
print("\n=== Generating AST ===")
generator = RegionASTGenerator(cfg, analyzer)
generator.regions = analyzer.regions

# Patch _process_if_blocks to trace
original_process = generator._process_if_blocks
def traced_process(blocks, region, branch='then'):
    print(f"\n[TRACE _process_if_blocks] branch={branch}, blocks={[b.start_offset for b in blocks]}")
    print(f"  region={type(region).__name__}, entry={region.entry.start_offset if region.entry else None}")
    print(f"  generated_blocks before: {sorted(b.start_offset for b in generator.generated_blocks)}")
    result = original_process(blocks, region, branch)
    print(f"  generated_blocks after: {sorted(b.start_offset for b in generator.generated_blocks)}")
    print(f"  result: {result}")
    return result
generator._process_if_blocks = traced_process

# Patch _generate_region to trace
original_gen = generator._generate_region
def traced_gen(region):
    print(f"\n[TRACE _generate_region] region={type(region).__name__}, entry={region.entry.start_offset if region.entry else None}")
    result = original_gen(region)
    print(f"  result: {result}")
    return result
generator._generate_region = traced_gen

try:
    ast_result = generator.generate()
    print(f"\n=== Final AST ===")
    import json
    print(json.dumps(ast_result, indent=2, default=str)[:3000])
except Exception as e:
    import traceback
    traceback.print_exc()
