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

for region in region_analyzer.regions:
    if type(region).__name__ == 'LoopRegion':
        print(f"LoopRegion:")
        print(f"  blocks: {sorted([b.id for b in region.blocks])}")
        print(f"  body_blocks: {sorted([b.id for b in region.body_blocks])}")
        print(f"  break_blocks: {sorted([b.id for b in region.break_blocks])}")
        print(f"  else_blocks: {sorted([b.id for b in region.else_blocks])}")
        
        # Check if break_blocks are in blocks
        for bb in region.break_blocks:
            in_blocks = bb in region.blocks
            in_body = bb in region.body_blocks
            print(f"  break_block {bb.id} (offset {bb.start_offset}): in_blocks={in_blocks}, in_body={in_body}")
