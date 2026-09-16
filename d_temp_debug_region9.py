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
        try_end_offset = try_region.try_offset_end
        
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
        
        # Check alternative_merges
        try_end_is_back_edge = False
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
        
        # So alternative_merges = [922, 940, 1070]
        # These are the outer try's handler blocks!
        # The problem: from_handler is True because handler block 618 jumps to 630,
        # and from 630 we can reach 922 through the if chain.
        # But 922 is the OUTER try's handler, not the merge point after the inner try.
        
        # The real merge point after the inner try-except-else is block 802
        # (the `if persist_provider:` block), which is INSIDE the outer try body.
        # The handler only reaches 922 via the exception edge.
        
        # So the problem is that alternative_merges includes blocks that are
        # reached via exception edges, not just normal control flow.
        # The code should exclude blocks that are exception handler entries.
        
        # Since alternative_merges = [922, ...] and try_end_is_back_edge=False,
        # the code sets merge_point = alternative_merges[0] = 922
        # Then: merge_point.start_offset (922) > precise_handler_end (622)
        # So it enters the else_blocks collection path
        
        if alternative_merges and not try_end_is_back_edge:
            merge_point = alternative_merges[0]
            print('Setting merge_point to %s (alternative_merge)' % merge_point.start_offset)
            
            # Now collect else_blocks between handler end and merge point
            else_blocks = []
            for block in cfg.get_blocks_in_order():
                if (block.start_offset > precise_handler_end and
                    block.start_offset < merge_point.start_offset and
                    block not in all_handler_blocks and
                    block not in try_region.blocks and
                    not analyzer._is_pass_or_return_none_block(block)):
                    _owner = analyzer.block_to_region.get(block)
                    if _owner is not None and _owner is not try_region:
                        if isinstance(_owner, (TryExceptRegion,)):
                            continue
                    else_blocks.append(block)
            print('else_blocks: %s' % sorted([b.start_offset for b in else_blocks]))
            # This should give: [630, 692, 732, 802, 806]
            # But 802 and 806 should NOT be here - they're after the inner try's else
