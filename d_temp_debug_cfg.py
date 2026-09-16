import sys, logging, marshal, types, dis
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
        print('Exception table raw hex:', co.co_exceptiontable.hex())
        
        # Check if cfg_builder reads it
        from core.cfg.cfg_builder import ControlFlowGraph
        cfg = ControlFlowGraph(co)
        print('cfg.exception_table type:', type(cfg.exception_table))
        print('cfg.exception_table len:', len(cfg.exception_table) if cfg.exception_table else 0)
        if cfg.exception_table:
            print('cfg.exception_table entries:')
            for i, entry in enumerate(cfg.exception_table):
                print('  [%d] %s' % (i, entry))
        
        # Also print block structure
        print('\nBlocks:')
        for block in cfg.get_blocks_in_order():
            last = block.get_last_instruction()
            last_str = '%s %s' % (last.opname, last.argval) if last else 'empty'
            print('  block %d: last=%s succ=%s' % (block.start_offset, last_str, [s.start_offset for s in block.successors]))
