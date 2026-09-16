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
        
        # Now trace _find_try_else_blocks step by step
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
        
        print('merge_point=%s' % (merge_point.start_offset if merge_point else None))
        print('precise_handler_end=%s' % precise_handler_end)
        
        # Since merge_point is None, we go to the Pattern TE path
        # Check try_end_is_back_edge
        try_end_is_back_edge = (
            try_end_block and try_end_block.instructions and
            any(i.opname == 'JUMP_BACKWARD' for i in try_end_block.instructions)
        )
        print('try_end_is_back_edge=%s' % try_end_is_back_edge)
        
        # Check alternative_merges
        alternative_merges = []
        for block in cfg.get_blocks_in_order():
            if (block.start_offset > precise_handler_end and
                block not in handler_blocks_set and
                block not in try_region.blocks):
                from_try = any(
                    analyzer._is_reachable_from(s, block, set())
                    for s in try_end_block.successors
                    if s not in handler_blocks_set
                )
                from_handler = any(
                    analyzer._is_reachable_from(hb, block, set())
                    for hb in handler_end_blocks
                )
                if from_try and from_handler:
                    alternative_merges.append(block)
        print('alternative_merges=%s' % sorted([b.start_offset for b in alternative_merges]))
        
        # Since alternative_merges might be empty (handler terminates), check Pattern TE
        if not alternative_merges and not try_end_is_back_edge:
            print('\nFalling to Pattern TE path...')
            _te_jf_target = None
            for _te_i in try_end_block.instructions:
                if _te_i.opname == 'JUMP_FORWARD':
                    _te_jf_target = _te_i.argval
                    break
            print('_te_jf_target=%s' % _te_jf_target)
            print('_te_jf_target > precise_handler_end: %s' % (_te_jf_target > precise_handler_end if _te_jf_target else False))
            
            if _te_jf_target is not None and _te_jf_target > precise_handler_end:
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
                print('_handler_also_jumps_to_target=%s' % _handler_also_jumps_to_target)
                
                # Check _te_target_reachable_from_handler
                _te_target_block = cfg.get_block_by_offset(_te_jf_target)
                from core.cfg.dominator_analyzer import BACKWARD_JUMP_OPS
                _te_handler_bfs_visited = set()
                _te_handler_bfs_queue = []
                for _, _, _hblocks_r51 in try_region.except_handlers:
                    for _hb_r51 in _hblocks_r51:
                        _te_handler_bfs_queue.append(_hb_r51)
                _te_target_reachable_from_handler = False
                while _te_handler_bfs_queue:
                    _hb_r51 = _te_handler_bfs_queue.pop(0)
                    if _hb_r51 in _te_handler_bfs_visited:
                        continue
                    _te_handler_bfs_visited.add(_hb_r51)
                    if _hb_r51.start_offset == _te_jf_target:
                        _te_target_reachable_from_handler = True
                        break
                    _hb_last_r51 = None
                    for _hb_i_r51 in reversed(_hb_r51.instructions):
                        if _hb_i_r51.opname in ('RESUME', 'NOP', 'CACHE'):
                            continue
                        _hb_last_r51 = _hb_i_r51
                        break
                    if (_hb_last_r51 is not None and
                            _hb_last_r51.opname in BACKWARD_JUMP_OPS):
                        continue
                    for _succ_r51 in _hb_r51.successors:
                        if _succ_r51 not in _te_handler_bfs_visited:
                            _te_handler_bfs_queue.append(_succ_r51)
                print('_te_target_reachable_from_handler=%s' % _te_target_reachable_from_handler)
                
                # Since _handler_also_jumps_to_target is True, the code takes this path:
                # "if not _handler_also_jumps_to_target and _te_target_reachable_from_handler:"
                # This is False, so the Pattern TE else collection is skipped
                
                # Then the code falls to the [try_end, first_handler) interval path
                handler_entry_offsets = []
                for heb in try_region.handler_entry_blocks:
                    if heb.start_offset >= try_end_offset:
                        handler_entry_offsets.append(heb.start_offset)
                first_handler_entry = min(handler_entry_offsets) if handler_entry_offsets else None
                print('\nfirst_handler_entry=%s' % first_handler_entry)
                print('try_end_offset=%s' % try_end_offset)
                
                if first_handler_entry is not None and first_handler_entry > try_end_offset:
                    print('[try_end, first_handler) = [%s, %s) - empty interval' % (try_end_offset, first_handler_entry))
                
                # Then falls to _find_inner_else_blocks
                print('\nCalling _find_inner_else_blocks...')
                inner_else = analyzer._find_inner_else_blocks(try_region, try_end_offset, all_handler_blocks)
                print('_find_inner_else_blocks result: %s' % (sorted([b.start_offset for b in inner_else]) if inner_else else 'None'))
