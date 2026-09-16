import sys, marshal, types, dis
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQData/utils/common_func.pyc'
with open(pyc, 'rb') as f:
    f.read(16)
    orig = marshal.load(f)

def extract(co):
    r = {}
    r[co.co_name or '<module>'] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r.update(extract(c))
    return r

om = extract(orig)
name = 'handle_exrights'
print('=== FULL ORIGINAL ===')
for i in dis.get_instructions(om[name]):
    a = f'{i.arg} ({i.argrepr})' if i.arg is not None and i.argrepr else (str(i.arg) if i.arg is not None else '')
    print(f'  {i.offset:4d} {i.opname:35s} {a}')
    if i.offset >= 110:
        break
