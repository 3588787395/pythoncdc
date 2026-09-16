import sys, logging, marshal, types, dis, traceback
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
        print('=== setup ===')
        # Try manually
        try:
            entries = list(dis._parse_exception_table(co))
            print('Manual parse OK, %d entries' % len(entries))
            for entry in entries:
                print('  start=%d end=%d target=%d depth=%d lasti=%s' % (entry.start, entry.end, entry.target, entry.depth, entry.lasti))
        except Exception as e:
            print('Manual parse failed:', e)
            traceback.print_exc()
        
        # Try cfg_builder with error
        from core.cfg.cfg_builder import CFGBuilder
        try:
            builder = CFGBuilder()
            builder.code_obj = co
            builder.cfg = None
            builder._parse_exception_table()
            print('\nCFGBuilder._parse_exception_table() result: %d entries' % (len(builder.cfg.exception_table) if builder.cfg else -1))
        except Exception as e:
            print('\nCFGBuilder._parse_exception_table() failed:', e)
            traceback.print_exc()
        
        # Try building full CFG
        try:
            cfg = CFGBuilder().build(co, 'setup')
            print('\nFull CFG build: exception_table=%d entries' % len(cfg.exception_table))
            print('Blocks: %d' % len(list(cfg.get_blocks_in_order())))
            for block in cfg.get_blocks_in_order():
                last = block.get_last_instruction()
                last_str = '%s %s' % (last.opname, last.argval) if last else 'empty'
                succs = [s.start_offset for s in block.successors]
                print('  block %d: last=%s succ=%s' % (block.start_offset, last_str, succs))
        except Exception as e:
            print('\nFull CFG build failed:', e)
            traceback.print_exc()
