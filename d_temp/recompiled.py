import py_compile, dis, marshal, types

# Compile the OK.py and check what bytecode is produced for handle_exrights
ok = 'F:/Downloads/pythoncdc-main/site-packages/IQData/utils/common_funcOK.py'
cf = py_compile.compile(ok, doraise=True, quiet=2)
if cf is None:
    import importlib.util
    cf = importlib.util.cache_from_source(ok)

with open(cf, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def extract(co):
    r = {}
    r[co.co_name or '<module>'] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r.update(extract(c))
    return r

om = extract(code)
name = 'handle_exrights'
print('=== RECOMPILED OK.py ===')
for i in dis.get_instructions(om[name]):
    a = f'{i.arg} ({i.argrepr})' if i.arg is not None and i.argrepr else (str(i.arg) if i.arg is not None else '')
    print(f'  {i.offset:4d} {i.opname:35s} {a}')
    if i.offset >= 110:
        break
