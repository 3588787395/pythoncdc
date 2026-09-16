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
        from core.cfg.dominator_analyzer import DominatorAnalyzer
        
        cfg = build_cfg(co, 'setup')
        analyzer = RegionAnalyzer(cfg)
        
        # Rebuild regions step by step
        regions = analyzer.analyze()
        
        inner_try = None
        outer_try = None
        for r in regions:
            if isinstance(r, TryExceptRegion):
                if r.try_offset_start == 444:
                    inner_try = r
                elif r.try_offset_start == 32:
                    outer_try = r
        
        # Simulate _find_try_else_blocks for inner try
        print('=== Simulating _find_try_else_blocks for inner try ===')
        
        try_region = inner_try
        
        # Check _try_body_terminates_abnormally
        print('Checking _try_body_terminates_abnormally...')
        # The try body is block 446, which ends with POP_TOP (not return/break/continue)
        # So it should NOT terminate abnormally
        
        try_end_offset = try_region.try_offset_end  # 526
        handler_blocks_set = set().union(*(set(h[2]) for h in try_region.except_handlers))
        all_handler_blocks = set(try_region.handler_entry_blocks) | handler_blocks_set
        
        # Handler end offsets
        handler_end_offsets = []
        for _, _, hblocks in try_region.except_handlers:
            if hblocks:
                last_handler_block = max(hblocks, key=lambda b: b.start_offset)
                if last_handler_block.instructions:
                    end_offset = last_handler_block.instructions[-1].offset + 2
                    handler_end_offsets.append(end_offset)
        precise_handler_end = max(handler_end_offsets) if handler_end_offsets else 0
        print('precise_handler_end=%s' % precise_handler_end)  # 622
        
        # Handler entry blocks check for JUMP_FORWARD targets
        for heb in try_region.handler_entry_blocks:
            if hasattr(heb, 'instructions') and heb.instructions:
                last_instr = heb.instructions[-1]
                if last_instr.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                    jump_target = last_instr.argval
                    if jump_target and jump_target > precise_handler_end:
                        precise_handler_end = jump_target
                        print('Updated precise_handler_end to %s from handler entry block %s' % (precise_handler_end, heb.start_offset))
        
        try_end_block = cfg.get_block_by_offset(try_end_offset)
        handler_end_blocks = [cfg.get_block_by_offset(offset) for offset in handler_end_offsets]
        handler_end_blocks = [b for b in handler_end_blocks if b is not None]
        
        all_exit_points = {try_end_block} | set(handler_end_blocks)
        dom_analyzer = DominatorAnalyzer(cfg)
        dom_analyzer.compute_post_dominators()
        merge_point = dom_analyzer.find_nearest_common_post_dominator(all_exit_points)
        
        print('all_exit_points=%s' % sorted([b.start_offset for b in all_exit_points]))
        print('merge_point=%s' % (merge_point.start_offset if merge_point else None))
        print('precise_handler_end=%s' % precise_handler_end)
        
        if merge_point:
            print('merge_point.start_offset > precise_handler_end: %s' % (merge_point.start_offset > precise_handler_end))
        
        # The merge_point should be block 802 or 922
        # Let's check
        if merge_point and merge_point.start_offset > precise_handler_end:
            # Find else blocks between handler end and merge point
            else_blocks = []
            for block in cfg.get_blocks_in_order():
                if (block.start_offset > precise_handler_end and
                    block.start_offset < merge_point.start_offset and
                    block not in all_handler_blocks and
                    block not in try_region.blocks and
                    not analyzer._is_pass_or_return_none_block(block)):
                    else_blocks.append(block)
            print('else_blocks from merge_point path: %s' % sorted([b.start_offset for b in else_blocks]))
        else:
            print('merge_point condition not met')
            
            # Check Pattern TE path
            # try_end_block has JUMP_FORWARD to 630
            _te_jf_target = None
            for _te_i in try_end_block.instructions:
                if _te_i.opname == 'JUMP_FORWARD':
                    _te_jf_target = _te_i.argval
                    break
            print('Pattern TE: try_end_block JUMP_FORWARD target = %s' % _te_jf_target)
            
            # Check _handler_also_jumps_to_target
            _handler_also_jumps_to_target = False
            for _, _, _hblocks in try_region.except_handlers:
                for _hb in _hblocks:
                    for _hb_i in _hb.instructions:
                        if _hb_i.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE') and _hb_i.argval == _te_jf_target:
                            _handler_also_jumps_to_target = True
                            break
                    if _handler_also_jumps_to_target:
                        break
                if _handler_also_jumps_to_target:
                    break
            print('_handler_also_jumps_to_target = %s' % _handler_also_jumps_to_target)
            
            # Since _handler_also_jumps_to_target is True, the Pattern TE path should NOT collect else blocks
            # Let's check the fallback path - the [try_end_offset, first_handler_entry) interval
            handler_entry_offsets = []
            for heb in try_region.handler_entry_blocks:
                if heb.start_offset >= try_end_offset:
                    handler_entry_offsets.append(heb.start_offset)
            first_handler_entry = min(handler_entry_offsets) if handler_entry_offsets else None
            print('first_handler_entry=%s' % first_handler_entry)
            print('try_end_offset=%s' % try_end_offset)
            
            if first_handler_entry is not None and first_handler_entry > try_end_offset:
                print('[try_end, first_handler) = [%s, %s)' % (try_end_offset, first_handler_entry))
                # This interval is [526, 528) which contains no blocks
                # So else_blocks should be empty from this path too
            
            # Check _find_inner_else_blocks
            inner_else = analyzer._find_inner_else_blocks(try_region, try_end_offset, all_handler_blocks)
            print('_find_inner_else_blocks result: %s' % sorted([b.start_offset for b in inner_else]) if inner_else else 'None')
