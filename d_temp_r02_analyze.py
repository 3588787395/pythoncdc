import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

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

for region in analyzer.regions:
    rtype = type(region).__name__
    if rtype == 'IfRegion':
        cond = getattr(region, 'condition_block', None)
        if cond:
            cond_last = cond.get_last_instruction()
            print('IfRegion: entry=%s, cond=%s, cond_last=%s arg=%s' % (
                region.entry.start_offset if region.entry else None,
                cond.start_offset,
                cond_last.opname if cond_last else None,
                cond_last.argval if cond_last else None))
            print('  then=%s' % [b.start_offset for b in region.then_blocks])
            print('  else=%s' % [b.start_offset for b in region.else_blocks])
            print('  merge=%s' % (region.merge_block.start_offset if region.merge_block else None))
            if cond_last and cond_last.argval is not None:
                jt = cfg.get_block_by_offset(cond_last.argval)
                then_offsets = set(b.start_offset for b in region.then_blocks)
                is_if_true = 'IF_TRUE' in cond_last.opname
                jumps_to_then = cond_last.argval in then_offsets
                print('  jump_target=%s, is_IF_TRUE=%s, jumps_to_then=%s' % (
                    jt.start_offset if jt else None, is_if_true, jumps_to_then))
            print()
    elif rtype == 'LoopRegion':
        print('LoopRegion: entry=%s, header=%s' % (
            region.entry.start_offset if region.entry else None,
            region.header_block.start_offset if region.header_block else None))
        print('  is_while_true=%s' % region.is_while_true)
        print('  cond_block=%s' % (region.condition_block.start_offset if region.condition_block else None))
        print('  body=%s' % [b.start_offset for b in region.body_blocks])
        print()
