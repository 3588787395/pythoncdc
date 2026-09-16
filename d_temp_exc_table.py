import sys, marshal, types, dis
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_persist/__init__.pyc'
with open(pyc, 'rb') as f:
    f.read(16); code = marshal.load(f)

# Print the exception table for setup function
def extract(co):
    r = {}; r[co.co_name or '<module>'] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType): r.update(extract(c))
    return r

for name, co in extract(code).items():
    if name == 'setup':
        print('=== setup exception table ===')
        print('co_exceptiontable:', co.co_exceptiontable)
        print()
        # Parse exception table entries
        from dis import _parse_exception_table
        try:
            et = _parse_exception_table(co)
            for entry in et:
                print('  start=%d end=%d target=%d depth=%d lasti=%s' % (entry.start, entry.end, entry.target, entry.depth, entry.lasti))
        except Exception as e:
            print('Error parsing:', e)
            # Manual parse
            import struct
            raw = co.co_exceptiontable
            print('Raw bytes:', raw.hex() if raw else 'empty')
