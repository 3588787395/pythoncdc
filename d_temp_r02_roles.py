import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, BoolOpRegion, BlockRole

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

# Block 50 successors
block_50 = cfg.get_block_by_offset(50)
for succ in block_50.successors:
    role = analyzer.get_block_role(succ)
    print("Block 50 successor: offset=%d role=%s" % (succ.start_offset, role))

# Block 168 role
block_168 = cfg.get_block_by_offset(168)
role_168 = analyzer.get_block_role(block_168)
print("Block 168 role: %s" % role_168)
print("Block 168 last instr:", block_168.get_last_instruction().opname, block_168.get_last_instruction().argval)

# Block 210 role
block_210 = cfg.get_block_by_offset(210)
role_210 = analyzer.get_block_role(block_210)
print("Block 210 role: %s" % role_210)

# Check the outer loop
for region in analyzer.regions:
    if isinstance(region, LoopRegion) and region.header_block and region.header_block.start_offset == 50:
        print()
        print("Loop with header=50:")
        print("  is_while_true=%s" % region.is_while_true)
        print("  cond_block=%s" % (region.condition_block.start_offset if region.condition_block else None))
        print("  back_edge=%s" % (region.back_edge_block.start_offset if region.back_edge_block else None))
        print("  break_blocks=%s" % [b.start_offset for b in region.break_blocks])
        print("  continue_map=%s" % region.continue_map if hasattr(region, 'continue_map') else 'N/A')
        break

# Find the outer loop
for region in analyzer.regions:
    if isinstance(region, LoopRegion) and region.header_block and region.header_block.start_offset == 48:
        print()
        print("Loop with header=48:")
        print("  is_while_true=%s" % region.is_while_true)
        print("  cond_block=%s" % (region.condition_block.start_offset if region.condition_block else None))
        print("  back_edge=%s" % (region.back_edge_block.start_offset if region.back_edge_block else None))
        break
