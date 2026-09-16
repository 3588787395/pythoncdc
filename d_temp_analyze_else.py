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
        
        # Test fix: compute handler_normal_exit_blocks instead of handler_end_blocks
        # These are the blocks that handlers normally jump to (via POP_EXCEPT + JUMP_FORWARD)
        # NOT the RERAISE cleanup blocks
        
        handler_normal_exit_blocks = []
        for _, _, hblocks in inner_try.except_handlers:
            for hb in hblocks:
                last = hb.get_last_instruction()
                if last and last.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                    # Handler exits normally via JUMP
                    target = last.argval
                    target_block = cfg.get_block_by_offset(target)
                    if target_block and target_block not in handler_normal_exit_blocks:
                        handler_normal_exit_blocks.append(target_block)
                elif last and last.opname == 'RETURN_VALUE':
                    pass  # Handler returns, no normal exit block
                elif last and last.opname == 'POP_EXCEPT':
                    # Check if next instruction is JUMP
                    # This handles the case where POP_EXCEPT and JUMP are in different blocks
                    for succ in hb.successors:
                        if succ not in hb.exception_successors:
                            if succ not in handler_normal_exit_blocks:
                                handler_normal_exit_blocks.append(succ)
        
        print('handler_normal_exit_blocks:', [b.start_offset for b in handler_normal_exit_blocks])
        # Should be [630] - the else clause entry
        
        # Now check: from_try for block 802
        try_end_block = cfg.get_block_by_offset(526)
        from_try_802 = analyzer._is_reachable_from(try_end_block, cfg.get_block_by_offset(802), set())
        print('from_try to 802: %s' % from_try_802)
        
        # from_handler for block 802 using normal exit blocks
        from_handler_802 = any(
            analyzer._is_reachable_from(hb, cfg.get_block_by_offset(802), set())
            for hb in handler_normal_exit_blocks
        )
        print('from_handler (normal exits) to 802: %s' % from_handler_802)
        
        # Check: from_handler for block 922 using normal exit blocks
        from_handler_922 = any(
            analyzer._is_reachable_from(hb, cfg.get_block_by_offset(922), set())
            for hb in handler_normal_exit_blocks
        )
        print('from_handler (normal exits) to 922: %s' % from_handler_922)
        
        # So with normal exit blocks:
        # - from_handler to 802: True (630 → 692 → 732 → 802)
        # - from_handler to 922: True (630 → 692 → 732 → 802 → 922 via exception)
        # Hmm, 922 is still reachable...
        
        # Actually the real issue is different. The handler's JUMP_FORWARD goes to 630,
        # which is the same target as the try body's JUMP_FORWARD.
        # Both the try body AND the handler converge at 630.
        # So 630 is actually the MERGE POINT, not the else entry!
        
        # Wait... In try-except-else, the else clause runs when try completes normally.
        # The handler runs when an exception occurs.
        # Both paths converge after the try-except-else block.
        
        # In this case:
        # - try body exits normally via JUMP_FORWARD to 630 (else clause)
        # - handler exits normally via POP_EXCEPT + JUMP_FORWARD to 630 (merge point)
        # 
        # But wait, the handler also jumps to 630? That means 630 is NOT the else clause
        # entry - it's the merge point after the try-except block!
        #
        # Actually no. In CPython's try-except-else bytecode:
        # try: body → JUMP_FORWARD to else_start
        # except: handler → POP_EXCEPT + JUMP_FORWARD to after_try
        # else: else_body → fall through to after_try
        #
        # When the handler jumps to 630 and the try body also jumps to 630,
        # it means there IS no else clause - 630 is the merge point.
        #
        # But the original source code HAS an else clause!
        # Let me re-examine...
        
        # Actually, let me re-read the OK.py more carefully
        print('\n=== Re-examining the structure ===')
        print('Original bytecode:')
        print('  444: NOP (inner try start)')
        print('  446-524: try body (strategy_log.warning + shutil.rmtree)')
        print('  526: JUMP_FORWARD 630 (skip handler, go to else)')
        print('  528-620: except BaseException handler')
        print('  618: POP_EXCEPT')
        print('  620: JUMP_FORWARD 630 (handler exits to merge point)')
        print('  622-628: RERAISE cleanup')
        print('  630-800: else clause + after-try code')
        print('  802-918: if persist_provider: ... (after inner try)')
        
        # So the handler's JUMP_FORWARD at offset 620 jumps to 630
        # The try body's JUMP_FORWARD at offset 526 also jumps to 630
        # 
        # When BOTH the try body and handler jump to the same target,
        # there is NO else clause in the bytecode sense!
        # The code at 630 is just the code after the try-except block.
        
        # But the original source has an else clause...
        # Let me check: does the Python compiler distinguish between
        # try-except-else and try-except in bytecode?
        
        # In CPython 3.11, try-except-else compiles as:
        # try: body → JUMP_FORWARD to else_start
        # except: handler → POP_EXCEPT → JUMP_FORWARD to after_block
        # else: else_body → fall through to after_block
        #
        # The try body jumps to else_start, handler jumps to after_block.
        # When there's no else: try body jumps to after_block, handler jumps to after_block.
        # Both jump to the same place!
        
        # So in this case, both try body (526) and handler (620) jump to 630.
        # This means in the original bytecode, there IS NO else clause!
        # The code at 630 is just regular code after the try-except.
        
        # But the OK.py has an else clause... Let me check if the OK.py is correct
        
        # Actually wait - the OK.py was GENERATED by the decompiler!
        # The question is: what does the ORIGINAL bytecode look like?
        # If both try body and handler jump to 630, then there's no else clause.
        # The decompiler should output:
        # try:
        #     strategy_log.warning(...)
        #     shutil.rmtree(dir_path)
        # except BaseException:
        #     system_log.error(...)
        # # After try-except:
        # if not os.path.exists(dir_path):
        #     os.makedirs(dir_path)
        # ...
        
        # But the OK.py has:
        # try:
        #     strategy_log.warning(...)
        #     shutil.rmtree(dir_path)
        # except BaseException:
        #     system_log.error(...)
        # else:
        #     if not os.path.exists(dir_path):
        #         os.makedirs(dir_path)
        #     ...
        
        # Both are semantically equivalent! The compiler produces the SAME bytecode
        # for both versions. So either output should match.
        
        # The issue is that the decompiler is choosing the "else" version,
        # which produces DIFFERENT bytecode when recompiled because the
        # compiler generates a JUMP_FORWARD that skips the except clause
        # and goes directly to the else clause (different from going to after-try).
