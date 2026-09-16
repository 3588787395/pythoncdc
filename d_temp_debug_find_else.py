import sys, logging, marshal, types
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

# Monkey-patch _find_try_else_blocks to add debug output
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion

_original_find_try_else = RegionAnalyzer._find_try_else_blocks

def _debug_find_try_else(self, try_region):
    if not hasattr(try_region, 'except_handlers') or not try_region.except_handlers:
        print('  [_find_try_else] No except_handlers, returning []')
        return []

    if self._try_body_terminates_abnormally(try_region):
        print('  [_find_try_else] try_body_terminates_abnormally, returning []')
        return []

    try_end_offset = try_region.try_offset_end
    print('  [_find_try_else] try_end_offset=%s' % try_end_offset)
    
    handler_blocks_set = set().union(*(set(h[2]) for h in try_region.except_handlers)) if try_region.except_handlers else set()
    all_handler_blocks = set()
    if try_region.handler_entry_blocks:
        all_handler_blocks.update(try_region.handler_entry_blocks)
    for _, _, hblocks in try_region.except_handlers:
        all_handler_blocks.update(hblocks)
    
    handler_end_offsets = []
    for _, _, hblocks in try_region.except_handlers:
        if hblocks:
            last_handler_block = max(hblocks, key=lambda b: b.start_offset)
            if last_handler_block.instructions:
                end_offset = last_handler_block.instructions[-1].offset + 2
                if end_offset not in handler_end_offsets:
                    handler_end_offsets.append(end_offset)
    
    precise_handler_end = max(handler_end_offsets) if handler_end_offsets else 0
    print('  [_find_try_else] precise_handler_end=%s (before handler entry check)' % precise_handler_end)
    
    for heb in try_region.handler_entry_blocks:
        if hasattr(heb, 'instructions') and heb.instructions:
            last_instr = heb.instructions[-1]
            if last_instr.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                jump_target = last_instr.argval
                if jump_target and jump_target > precise_handler_end:
                    precise_handler_end = jump_target
                    print('  [_find_try_else] Updated precise_handler_end=%s from handler entry' % precise_handler_end)
    
    try_end_block = self.cfg.get_block_by_offset(try_end_offset)
    handler_end_blocks = [self.cfg.get_block_by_offset(offset) for offset in handler_end_offsets]
    handler_end_blocks = [b for b in handler_end_blocks if b is not None]
    
    if not handler_end_blocks or try_end_block is None:
        print('  [_find_try_else] No handler_end_blocks or try_end_block, returning []')
        return []
    
    all_exit_points = {try_end_block} | set(handler_end_blocks)
    merge_point = self.dom_analyzer.find_nearest_common_post_dominator(all_exit_points)
    print('  [_find_try_else] merge_point=%s' % (merge_point.start_offset if merge_point else None))
    
    if not merge_point or merge_point.start_offset <= precise_handler_end:
        try_end_is_back_edge = (
            try_end_block and try_end_block.instructions and
            any(i.opname == 'JUMP_BACKWARD' for i in try_end_block.instructions)
        )
        print('  [_find_try_else] try_end_is_back_edge=%s' % try_end_is_back_edge)
        
        alternative_merges = []
        for block in self.cfg.get_blocks_in_order():
            if (block.start_offset > precise_handler_end and
                block not in handler_blocks_set and
                block not in try_region.blocks):
                from_try = any(
                    self._is_reachable_from(s, block, set())
                    for s in try_end_block.successors
                    if s not in handler_blocks_set
                )
                from_handler = any(
                    self._is_reachable_from(hb, block, set())
                    for hb in handler_end_blocks
                )
                if from_try and from_handler:
                    alternative_merges.append(block)
        
        print('  [_find_try_else] alternative_merges=%s' % sorted([b.start_offset for b in alternative_merges]))
        
        if alternative_merges and not try_end_is_back_edge:
            merge_point = alternative_merges[0]
            print('  [_find_try_else] Set merge_point=%s from alternative_merges' % merge_point.start_offset)
        else:
            # Pattern TE path
            print('  [_find_try_else] Entering Pattern TE path...')
            _te_else_blocks = []
            if (try_end_block and try_end_block.instructions and
                    not try_end_is_back_edge):
                _te_jf_target = None
                for _te_i in try_end_block.instructions:
                    if _te_i.opname == 'JUMP_FORWARD':
                        _te_jf_target = _te_i.argval
                        break
                print('  [_find_try_else] _te_jf_target=%s' % _te_jf_target)
                
                if (_te_jf_target is not None and
                        _te_jf_target > precise_handler_end):
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
                    print('  [_find_try_else] _handler_also_jumps_to_target=%s' % _handler_also_jumps_to_target)
                    
                    # R51 check
                    from core.cfg.dominator_analyzer import BACKWARD_JUMP_OPS
                    _te_target_reachable_from_handler = False
                    _te_handler_bfs_visited = set()
                    _te_handler_bfs_queue = []
                    for _, _, _hblocks_r51 in try_region.except_handlers:
                        for _hb_r51 in _hblocks_r51:
                            _te_handler_bfs_queue.append(_hb_r51)
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
                    print('  [_find_try_else] _te_target_reachable_from_handler=%s' % _te_target_reachable_from_handler)
                    
                    if not _handler_also_jumps_to_target and _te_target_reachable_from_handler:
                        print('  [_find_try_else] Taking Pattern TE else collection path')
                    else:
                        print('  [_find_try_else] NOT taking Pattern TE path (handler_also_jumps=%s, target_reachable=%s)' % (_handler_also_jumps_to_target, _te_target_reachable_from_handler))
            
            if not _te_else_blocks:
                # [try_end, first_handler) interval path
                handler_entry_offsets = []
                for heb in try_region.handler_entry_blocks:
                    if heb.start_offset >= try_end_offset:
                        handler_entry_offsets.append(heb.start_offset)
                first_handler_entry = min(handler_entry_offsets) if handler_entry_offsets else None
                print('  [_find_try_else] first_handler_entry=%s, try_end_offset=%s' % (first_handler_entry, try_end_offset))
                
                if first_handler_entry is not None and first_handler_entry > try_end_offset:
                    print('  [_find_try_else] [try_end, first_handler) = [%s, %s) - checking for else blocks' % (try_end_offset, first_handler_entry))
                else:
                    print('  [_find_try_else] [try_end, first_handler) interval is empty')
            
            # _find_inner_else_blocks
            print('  [_find_try_else] Calling _find_inner_else_blocks...')
            inner_else = self._find_inner_else_blocks(try_region, try_end_offset, all_handler_blocks)
            print('  [_find_try_else] _find_inner_else_blocks returned: %s' % sorted([b.start_offset for b in inner_else]) if inner_else else '[]')
            
            if _te_else_blocks:
                return _te_else_blocks
            
            if inner_else:
                return inner_else
            
            return []
    
    # merge_point exists and > precise_handler_end
    print('  [_find_try_else] merge_point=%s > precise_handler_end=%s, collecting else_blocks' % (merge_point.start_offset, precise_handler_end))
    else_blocks = []
    for block in self.cfg.get_blocks_in_order():
        if (block.start_offset > precise_handler_end and
            block.start_offset < merge_point.start_offset and
            block not in all_handler_blocks and
            block not in try_region.blocks and
            not self._is_pass_or_return_none_block(block)):
            _owner = self.block_to_region.get(block)
            if _owner is not None and _owner is not try_region:
                if isinstance(_owner, (TryExceptRegion,)):
                    continue
            else_blocks.append(block)
    print('  [_find_try_else] else_blocks from merge_point path: %s' % sorted([b.start_offset for b in else_blocks]))
    
    if not else_blocks:
        handler_entry_offsets = []
        for heb in try_region.handler_entry_blocks:
            if heb.start_offset >= try_end_offset:
                handler_entry_offsets.append(heb.start_offset)
        first_handler_entry = min(handler_entry_offsets) if handler_entry_offsets else None
        if first_handler_entry is not None and first_handler_entry > try_end_offset:
            print('  [_find_try_else] Checking R118 [try_end, first_handler) path...')
    
    if not else_blocks:
        inner_else = self._find_inner_else_blocks(try_region, try_end_offset, all_handler_blocks)
        if inner_else:
            return inner_else
    
    return else_blocks

RegionAnalyzer._find_try_else_blocks = _debug_find_try_else

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
