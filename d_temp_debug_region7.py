import sys, logging, marshal, types
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

logging.basicConfig(level=logging.WARNING)

pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_persist/__init__.pyc'
with open(pyc, 'rb') as f:
    f.read(16); code = marshal.load(f)

def extract(co):
    r = {}; r[co.co_name or '<module>'] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType): r.update(extract(c))
    return r

for name, co in extract(code).items():
    if name == 'setup':
        from core.cfg.cfg_builder import build_cfg
        from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion
        
        cfg = build_cfg(co, 'setup')
        analyzer = RegionAnalyzer(cfg)
        regions = analyzer.analyze()
        
        inner_try = None
        for r in regions:
            if isinstance(r, TryExceptRegion) and r.try_offset_start == 444:
                inner_try = r
        
        try_region = inner_try
        try_end_offset = try_region.try_offset_end  # 526
        handler_blocks_set = set().union(*(set(h[2]) for h in try_region.except_handlers))
        all_handler_blocks = set(try_region.handler_entry_blocks) | handler_blocks_set
        
        handler_end_offsets = []
        for _, _, hblocks in try_region.except_handlers:
            if hblocks:
                last_handler_block = max(hblocks, key=lambda b: b.start_offset)
                if last_handler_block.instructions:
                    end_offset = last_handler_block.instructions[-1].offset + 2
                    handler_end_offsets.append(end_offset)
        precise_handler_end = max(handler_end_offsets) if handler_end_offsets else 0
        
        for heb in try_region.handler_entry_blocks:
            if hasattr(heb, 'instructions') and heb.instructions:
                last_instr = heb.instructions[-1]
                if last_instr.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                    jump_target = last_instr.argval
                    if jump_target and jump_target > precise_handler_end:
                        precise_handler_end = jump_target
        
        try_end_block = cfg.get_block_by_offset(try_end_offset)
        handler_end_blocks = [cfg.get_block_by_offset(offset) for offset in handler_end_offsets]
        handler_end_blocks = [b for b in handler_end_blocks if b is not None]
        
        all_exit_points = {try_end_block} | set(handler_end_blocks)
        merge_point = analyzer.dom_analyzer.find_nearest_common_post_dominator(all_exit_points)
        
        print('all_exit_points=%s' % sorted([b.start_offset for b in all_exit_points]))
        print('merge_point=%s' % (merge_point.start_offset if merge_point else None))
        print('precise_handler_end=%s' % precise_handler_end)
        
        if merge_point:
            print('merge_point > precise_handler_end: %s' % (merge_point.start_offset > precise_handler_end))
            
            if merge_point.start_offset > precise_handler_end:
                else_blocks = []
                for block in cfg.get_blocks_in_order():
                    if (block.start_offset > precise_handler_end and
                        block.start_offset < merge_point.start_offset and
                        block not in all_handler_blocks and
                        block not in try_region.blocks and
                        not analyzer._is_pass_or_return_none_block(block)):
                        _owner = analyzer.block_to_region.get(block)
                        if _owner is not None and _owner is not try_region:
                            if isinstance(_owner, TryExceptRegion):
                                continue
                        else_blocks.append(block)
                print('else_blocks from merge_point path: %s' % sorted([b.start_offset for b in else_blocks]))
            else:
                print('merge_point <= precise_handler_end, checking other paths...')
        else:
            print('No merge_point found')
