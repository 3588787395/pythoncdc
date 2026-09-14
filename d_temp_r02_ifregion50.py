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

# Find the inner loop with header=50
inner_loop = None
for region in analyzer.regions:
    if isinstance(region, LoopRegion) and region.header_block and region.header_block.start_offset == 50:
        inner_loop = region
        break

if inner_loop:
    print("Inner loop (header=50):")
    print("  is_while_true=%s" % inner_loop.is_while_true)
    print("  cond_block=%s" % (inner_loop.condition_block.start_offset if inner_loop.condition_block else None))
    
    # Check if there's an IfRegion with entry/condition_block == block 50
    block_50 = cfg.get_block_by_offset(50)
    _header_if_region = None
    for _r in inner_loop.iter_descendants((IfRegion,)):
        if _r.condition_block == block_50 or _r.entry == block_50:
            _header_if_region = _r
            break
    
    if _header_if_region:
        print("  Found IfRegion with entry/cond=50:")
        print("    entry=%s cond=%s" % (_header_if_region.entry.start_offset if _header_if_region.entry else None,
                                        _header_if_region.condition_block.start_offset if _header_if_region.condition_block else None))
        print("    then=%s" % [b.start_offset for b in _header_if_region.then_blocks])
        print("    else=%s" % [b.start_offset for b in _header_if_region.else_blocks])
    else:
        print("  No IfRegion with entry/cond=50 found in inner loop descendants")
    
    # Also check the outer loop
    outer_loop = None
    for region in analyzer.regions:
        if isinstance(region, LoopRegion) and region.header_block and region.header_block.start_offset == 48:
            outer_loop = region
            break
    
    if outer_loop:
        _header_if_region2 = None
        for _r in outer_loop.iter_descendants((IfRegion,)):
            if _r.condition_block == block_50 or _r.entry == block_50:
                _header_if_region2 = _r
                break
        if _header_if_region2:
            print("  Found IfRegion with entry/cond=50 in OUTER loop descendants:")
            print("    entry=%s cond=%s" % (_header_if_region2.entry.start_offset if _header_if_region2.entry else None,
                                            _header_if_region2.condition_block.start_offset if _header_if_region2.condition_block else None))
        else:
            print("  No IfRegion with entry/cond=50 found in outer loop descendants either")
    
    # Check all regions for block 50
    for r in analyzer.regions:
        if isinstance(r, IfRegion) and (r.entry == block_50 or r.condition_block == block_50):
            print("  IfRegion in global list with entry/cond=50: entry=%s cond=%s" % (
                r.entry.start_offset if r.entry else None,
                r.condition_block.start_offset if r.condition_block else None))
