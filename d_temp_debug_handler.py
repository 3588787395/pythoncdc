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
        
        # Check why handler_end_blocks can reach 922
        # handler_end_blocks = [block at offset 622] (the RERAISE block)
        block_622 = cfg.get_block_by_offset(622)
        print('Block 622 instructions:')
        for instr in block_622.instructions:
            print('  %4d %s %s' % (instr.offset, instr.opname, instr.argval))
        print('Block 622 successors:', [s.start_offset for s in block_622.successors])
        print('Block 622 exception_successors:', [s.start_offset for s in block_622.exception_successors])
        
        # Block 624 is the cleanup block after handler
        block_624 = cfg.get_block_by_offset(624)
        print('\nBlock 624 instructions:')
        for instr in block_624.instructions:
            print('  %4d %s %s' % (instr.offset, instr.opname, instr.argval))
        print('Block 624 successors:', [s.start_offset for s in block_624.successors])
        print('Block 624 exception_successors:', [s.start_offset for s in block_624.exception_successors])
        
        # The handler_end_block is at offset 622 (last instruction of handler)
        # Block 622 (RERAISE 0) has successor 624 (RERAISE 1) which has successor 922
        # So from_handler=True for 922
        
        # The issue: handler_end_blocks should be the blocks at the END of the handler
        # Not the RERAISE cleanup blocks
        # Let me check what handler_end_offsets are
        print('\nHandler blocks for inner try:')
        analyzer = RegionAnalyzer(cfg)
        regions = analyzer.analyze()
        
        inner_try = None
        for r in regions:
            if isinstance(r, TryExceptRegion) and r.try_offset_start == 444:
                inner_try = r
        
        for ht, hn, hb in inner_try.except_handlers:
            print('Handler type=%s blocks=%s' % (ht, sorted([b.start_offset for b in hb])))
            for b in hb:
                last = b.get_last_instruction()
                print('  Block %d last=%s %s' % (b.start_offset, last.opname if last else 'none', last.argval if last else ''))
        
        # The except_handlers include blocks [546, 618]
        # Block 546: POP_TOP ... CALL ... POP_TOP (the actual handler code)
        # Block 618: POP_EXCEPT + JUMP_FORWARD 630 (handler exit)
        # But block 622 and 624 are NOT in the handler body!
        # They are cleanup blocks after the handler
        
        # However, handler_end_offsets is calculated from the last handler block's last instruction offset
        # Block 618's last instruction is at offset 620, so end_offset = 620 + 2 = 622
        # Then handler_end_blocks = [block at offset 622]
        # But block 622 is a RERAISE cleanup block, not part of the handler!
        
        # The real handler exit is block 618 which ends with POP_EXCEPT + JUMP_FORWARD 630
        # This jumps to the else clause (630), not to a merge point
        
        # So handler_end_blocks should really be [618], not [622]
        # The problem is that handler_end_offsets uses the instruction offset + 2
        # which points to the NEXT instruction after the handler body
        # That next instruction happens to be in a cleanup block (RERAISE)
