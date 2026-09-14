import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, BoolOpRegion, BlockRole
from core.cfg.region_ast_generator import RegionASTGenerator

import marshal, types

with open('site-packages/IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(code_obj, name):
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            result = find_code(const, name)
            if result:
                return result
    return None

tick = find_code(code, 'tick_worker_thread')

builder = CFGBuilder()
cfg = builder.build(tick)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Check the role of block 168 (the continue block)
block_168 = cfg.get_block_by_offset(168)
role_168 = analyzer.get_block_role(block_168)
print("Block 168 role:", role_168)

# Check the role of block 210 (the then body start)
block_210 = cfg.get_block_by_offset(210)
role_210 = analyzer.get_block_role(block_210)
print("Block 210 role:", role_210)

# Check block 50's role
block_50 = cfg.get_block_by_offset(50)
role_50 = analyzer.get_block_role(block_50)
print("Block 50 role:", role_50)

# Find all IfRegions that have then_blocks containing block 168 or 210
print()
print("=== IfRegions containing block 168 or 210 in then/else ===")
for region in analyzer.regions:
    if isinstance(region, IfRegion):
        then_offsets = [b.start_offset for b in region.then_blocks]
        else_offsets = [b.start_offset for b in region.else_blocks]
        if 168 in then_offsets or 168 in else_offsets or 210 in then_offsets or 210 in else_offsets:
            print("IfRegion entry=%s cond=%s" % (
                region.entry.start_offset if region.entry else None,
                region.condition_block.start_offset if region.condition_block else None))
            print("  then=%s" % then_offsets)
            print("  else=%s" % else_offsets)
