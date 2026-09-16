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
        
        # Check inner_try's blocks attribute
        print('inner_try.blocks: %s' % sorted([b.start_offset for b in inner_try.blocks]))
        print('inner_try.try_blocks: %s' % sorted([b.start_offset for b in inner_try.try_blocks]))
        print('inner_try.else_blocks: %s' % sorted([b.start_offset for b in inner_try.else_blocks]))
        
        # The issue: blocks 630, 692, 732, 802, 806 are NOT in inner_try.blocks
        # They ARE in inner_try.else_blocks
        # But they should be in inner_try.blocks (because they're in the outer try body)
        
        # Wait, if they're in else_blocks, then they should also be in blocks
        # Let me check the code flow in region_analyzer.py around line 8140-8150
        # After _find_try_else_blocks, else_blocks are added to region.blocks
        
        # The real question is: why are blocks 802 and 806 in the inner try's else_blocks?
        # In the OK.py, the inner try-except-else has these else blocks:
        # else:
        #     if not os.path.exists(dir_path):
        #         os.makedirs(dir_path)
        #     persist_provider = JsonPersistance(dir_path)
        #     self._recorder = CsvRecorder(dir_path)
        # This is blocks 630, 692, 732
        
        # Block 802 is `if persist_provider:` which is AFTER the inner try-except-else
        # It should be in the OUTER try body, not the inner try's else
        
        # The problem is in the BFS collection of else blocks from the JUMP_FORWARD target
        # When the handler also jumps to the same target (630), the Pattern TE path is skipped
        # But alternative_merges leads to collecting blocks up to the merge point (922)
        # which includes too many blocks
        
        # Let me check what path _find_try_else_blocks actually takes
        # by adding print statements to the actual function
        
        # Actually, let me just check if the inner try region was created BEFORE the outer try
        # If so, the inner try's else_blocks might have been set before the outer try region
        # consumed the outer try body blocks
        
        # Check block_to_region for blocks 630, 692, 732, 802, 806
        for offset in [630, 692, 732, 802, 806]:
            block = cfg.get_block_by_offset(offset)
            if block:
                owner = analyzer.block_to_region.get(block)
                print('Block %d owner: %s (id=%s)' % (offset, type(owner).__name__ if owner else None, id(owner) if owner else None))
        
        print('\ninner_try id: %s' % id(inner_try))
        
        # Also check what the outer try looks like
        outer_try = None
        for r in regions:
            if isinstance(r, TryExceptRegion) and r.try_offset_start == 32:
                outer_try = r
        
        if outer_try:
            print('outer_try id: %s' % id(outer_try))
            print('outer_try.try_blocks: %s' % sorted([b.start_offset for b in outer_try.try_blocks]))
            print('outer_try.else_blocks: %s' % sorted([b.start_offset for b in outer_try.else_blocks]))
