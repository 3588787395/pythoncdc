import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, BoolOpRegion

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

# Find block 50
block_50 = cfg.get_block_by_offset(50)
print("Block 50 last instr:", block_50.get_last_instruction().opname, block_50.get_last_instruction().argval)

# Check which region owns block 50
for region in analyzer.regions:
    if hasattr(region, 'blocks') and block_50 in region.blocks:
        rtype = type(region).__name__
        if rtype == 'IfRegion':
            print("Block 50 is in IfRegion entry=%s cond=%s" % (
                region.entry.start_offset if region.entry else None,
                region.condition_block.start_offset if region.condition_block else None))
            print("  then=%s" % [b.start_offset for b in region.then_blocks])
            print("  else=%s" % [b.start_offset for b in region.else_blocks])
            cond_last = region.condition_block.get_last_instruction() if region.condition_block else None
            print("  cond_last=%s %s" % (cond_last.opname if cond_last else None, cond_last.argval if cond_last else None))
        elif rtype == 'LoopRegion':
            print("Block 50 is in LoopRegion entry=%s header=%s is_while_true=%s" % (
                region.entry.start_offset if region.entry else None,
                region.header_block.start_offset if region.header_block else None,
                region.is_while_true))
            print("  cond_block=%s" % (region.condition_block.start_offset if region.condition_block else None))

print()
print("=== Now check which IfRegion has entry=50 ===")
for region in analyzer.regions:
    if isinstance(region, IfRegion):
        if region.entry and region.entry.start_offset == 50:
            print("Found IfRegion with entry=50")
            print("  cond=%s" % (region.condition_block.start_offset if region.condition_block else None))
            print("  then=%s" % [b.start_offset for b in region.then_blocks])
            print("  else=%s" % [b.start_offset for b in region.else_blocks])
            cond_last = region.condition_block.get_last_instruction() if region.condition_block else None
            print("  cond_last=%s %s" % (cond_last.opname if cond_last else None, cond_last.argval if cond_last else None))
