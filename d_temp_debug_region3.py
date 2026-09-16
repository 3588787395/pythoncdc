import sys, logging, marshal, types
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

logging.basicConfig(level=logging.DEBUG, format='%(name)s: %(message)s')

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
        from core.cfg.cfg_builder import ControlFlowGraph, build_cfg
        from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion
        
        cfg = build_cfg(co, 'setup')
        analyzer = RegionAnalyzer(cfg)
        regions = analyzer.analyze()
        
        print('\n=== Regions for setup ===')
        for i, r in enumerate(regions):
            rtype = type(r).__name__
            entry_off = r.entry.start_offset if r.entry else None
            if isinstance(r, TryExceptRegion):
                print('\nRegion %d: %s entry=%s' % (i, rtype, entry_off))
                print('  try_offset_start=%s try_offset_end=%s' % (r.try_offset_start, r.try_offset_end))
                print('  try_blocks=%s' % sorted([b.start_offset for b in r.try_blocks]))
                print('  has_else=%s' % getattr(r, 'has_else', False))
                else_blks = getattr(r, 'else_blocks', [])
                print('  else_blocks=%s' % sorted([b.start_offset for b in else_blks]))
                print('  except_handlers:')
                for ht, hn, hb in getattr(r, 'except_handlers', []):
                    print('    type=%s name=%s blocks=%s' % (ht, hn, sorted([b.start_offset for b in hb])))
                print('  handler_entry_blocks=%s' % sorted([b.start_offset for b in getattr(r, 'handler_entry_blocks', [])]))
                fb = getattr(r, 'finally_blocks', None)
                if fb:
                    print('  finally_blocks=%s' % sorted([b.start_offset for b in fb]))
            else:
                print('\nRegion %d: %s entry=%s blocks=%s' % (i, rtype, entry_off, 
                    sorted([b.start_offset for b in r.blocks]) if hasattr(r, 'blocks') else ''))
