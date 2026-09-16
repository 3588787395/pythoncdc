import sys, logging, marshal, types
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

# Only show warnings and above
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
        
        # Get inner try region
        inner_try = None
        outer_try = None
        for r in regions:
            if isinstance(r, TryExceptRegion):
                if r.try_offset_start == 444:
                    inner_try = r
                elif r.try_offset_start == 32:
                    outer_try = r
        
        print('Inner try region:')
        print('  try_offset_end=%s' % inner_try.try_offset_end)
        print('  handler_entry_blocks=%s' % sorted([b.start_offset for b in inner_try.handler_entry_blocks]))
        print('  else_blocks=%s' % sorted([b.start_offset for b in inner_try.else_blocks]))
        
        # Check where block 802 should belong
        # In original bytecode, offset 802 is where the inner try-except-else ends
        # and the `if persist_provider:` block starts
        # Let's look at exception table entries
        print('\nException table entries covering inner try:')
        for entry in cfg.exception_table:
            if entry['start'] <= 802 <= entry['end'] or entry['start'] <= 630 <= entry['end']:
                print('  start=%d end=%d target=%d depth=%d' % (entry['start'], entry['end'], entry['target'], entry['depth']))
        
        # Check block 802's successors
        for block in cfg.get_blocks_in_order():
            if block.start_offset == 802:
                print('\nBlock 802:')
                for instr in block.instructions:
                    print('  %4d %s %s' % (instr.offset, instr.opname, instr.argval))
                print('  successors:', [s.start_offset for s in block.successors])
        
        # Check the handler of inner try
        print('\nInner try except handler:')
        for ht, hn, hb in inner_try.except_handlers:
            for b in hb:
                print('  Block %d:' % b.start_offset)
                for instr in b.instructions:
                    print('    %4d %s %s' % (instr.offset, instr.opname, instr.argval))
