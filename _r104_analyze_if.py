import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole
import marshal

path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_09_multi_elif_break.pyc'
with open(path, 'rb') as f:
    f.read(4); f.read(4); f.read(8)
    code = marshal.load(f)

func_code = code.co_consts[1]
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(func_code)

region_analyzer = RegionAnalyzer(cfg)
regions = region_analyzer.analyze()

# Find the IF_THEN region (entry=block 3)
for region in regions:
    if type(region).__name__ == 'IfRegion' and region.region_type.name == 'IF_THEN':
        print(f"IfRegion (IF_THEN):")
        print(f"  entry: block {region.entry.id if hasattr(region.entry, 'id') else '?'}")
        print(f"  condition_block: {region.condition_block}")
        print(f"  then_blocks: {region.then_blocks}")
        print(f"  else_blocks: {region.else_blocks}")
        print(f"  has_else: {region.has_else}")
        print(f"  merge_block: {region.merge_block}")
        print(f"  blocks: {region.blocks}")
        
        # Check block 9
        for b in region.else_blocks:
            print(f"\n  Else block {b.id} (offset {b.start_offset}):")
            print(f"    instructions: {[(i.opname, i.arg) for i in b.instructions]}")
            print(f"    successors: {b.successors}")
            role = region_analyzer.get_block_role(b)
            print(f"    role: {role}")
            print(f"    in generated_blocks: {b in region_analyzer.generated_blocks if hasattr(region_analyzer, 'generated_blocks') else 'N/A'}")
