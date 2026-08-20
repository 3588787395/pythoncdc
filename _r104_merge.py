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
region_analyzer.analyze()
region_analyzer._annotate_all_roles(region_analyzer.regions)

# Get blocks
block3 = cfg.blocks[3]  # condition
block4 = cfg.blocks[4]  # then_succ
block9 = cfg.blocks[9]  # else_succ

# Test _compute_merge_from_jump_targets
result = region_analyzer._compute_merge_from_jump_targets(block3, block4, block9)
print(f"_compute_merge_from_jump_targets result: {result}")
if result:
    print(f"  result block: {result.id}, offset: {result.start_offset}")

# Check NCPD
ncpd = region_analyzer._nearest_common_post_dominator(block4, block9) if hasattr(region_analyzer, '_nearest_common_post_dominator') else 'N/A'
print(f"NCPD(then_succ, else_succ): {ncpd}")

# Check block 9 predecessors
print(f"\nBlock 9 predecessors: {[p.id for p in block9.predecessors]}")
print(f"Block 9 instructions: {[(i.opname, i.arg) for i in block9.instructions]}")
print(f"Block 9 role: {region_analyzer.get_block_role(block9)}")

# Check if block 9 is in break_blocks of loop region
for region in region_analyzer.regions:
    if type(region).__name__ == 'LoopRegion':
        print(f"\nLoopRegion:")
        print(f"  body_blocks: {[b.id for b in region.body_blocks]}")
        print(f"  break_blocks: {[b.id for b in region.break_blocks] if hasattr(region, 'break_blocks') else 'N/A'}")
        print(f"  else_blocks: {[b.id for b in region.else_blocks]}")
        print(f"  header_block: {region.header_block.id if region.header_block else None}")
