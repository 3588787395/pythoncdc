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
        from core.cfg.basic_block import BasicBlock
        
        cfg = build_cfg(co, 'setup')
        analyzer = RegionAnalyzer(cfg)
        regions = analyzer.analyze()
        
        inner_try = None
        for r in regions:
            if isinstance(r, TryExceptRegion) and r.try_offset_start == 444:
                inner_try = r
        
        # Find precise_handler_end for inner try
        handler_end_offsets = []
        for _, _, hblocks in inner_try.except_handlers:
            if hblocks:
                last_handler_block = max(hblocks, key=lambda b: b.start_offset)
                if last_handler_block.instructions:
                    end_offset = last_handler_block.instructions[-1].offset + 2
                    handler_end_offsets.append(end_offset)
        precise_handler_end = max(handler_end_offsets) if handler_end_offsets else 0
        print('precise_handler_end=%s' % precise_handler_end)
        
        # Check the try_end_block
        try_end_offset = inner_try.try_offset_end
        print('try_end_offset=%s' % try_end_offset)
        try_end_block = cfg.get_block_by_offset(try_end_offset)
        print('try_end_block=%s' % (try_end_block.start_offset if try_end_block else None))
        
        if try_end_block:
            for instr in try_end_block.instructions:
                print('  %4d %s %s' % (instr.offset, instr.opname, instr.argval))
            print('  successors:', [s.start_offset for s in try_end_block.successors])
        
        # Check what _find_try_else_blocks would do
        # The handler at block 618 ends with JUMP_FORWARD to 630
        # Block 630 starts the else clause
        # But the else clause should end where the inner try region ends
        # In the original bytecode, the inner try covers offsets 444-802 (with else)
        # And the outer try continues from 802 to 914
        
        # The key issue: blocks 802 and 806 are part of the outer try body
        # but are being included in inner try's else_blocks
        # Block 802: if persist_provider: ...
        # This should NOT be in the inner try's else clause
        
        # Let's check what the handler's JUMP_FORWARD target is
        handler_blocks_set = set().union(*(set(h[2]) for h in inner_try.except_handlers))
        all_handler_blocks = set(inner_try.handler_entry_blocks) | handler_blocks_set
        print('\nAll handler blocks:', sorted([b.start_offset for b in all_handler_blocks]))
        
        # Check handler exit jump
        for _, _, hb in inner_try.except_handlers:
            for b in hb:
                last = b.get_last_instruction()
                if last and last.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                    print('Handler block %d JUMP to %s' % (b.start_offset, last.argval))
        
        # Check _handler_also_jumps_to_target
        # try_end_block (526) jumps to 630
        # handler block 618 also jumps to 630
        # So _handler_also_jumps_to_target should be True!
        # That means the else blocks should NOT be collected via the Pattern TE path
        print('\nChecking _handler_also_jumps_to_target:')
        _te_jf_target = 630  # JUMP_FORWARD target from try_end_block
        for _, _, _hblocks in inner_try.except_handlers:
            for _hb in _hblocks:
                for _hb_i in _hb.instructions:
                    if _hb_i.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE') and _hb_i.argval == _te_jf_target:
                        print('  Handler block %d also jumps to %d!' % (_hb.start_offset, _te_jf_target))
