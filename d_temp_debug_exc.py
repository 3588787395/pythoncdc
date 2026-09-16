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
        print('=== setup ===')
        print('co_exceptiontable bytes:', co.co_exceptiontable.hex() if co.co_exceptiontable else 'empty')
        print('len:', len(co.co_exceptiontable))
        
        from dis import _parse_exception_table
        try:
            et = _parse_exception_table(co)
            print('Parsed entries:')
            for entry in et:
                print('  start=%d end=%d target=%d depth=%d lasti=%s' % (entry.start, entry.end, entry.target, entry.depth, entry.lasti))
        except Exception as e:
            print('Error:', e)
