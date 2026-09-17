import dis, types, marshal

pyc = 'F:/Downloads/pythoncdc-main/site-packages/fly/common/tradingday_calendar.pyc'
ok = pyc.replace('.pyc', 'OK.py')

with open(pyc, 'rb') as f:
    f.read(16); orig = marshal.load(f)
import py_compile
cf = py_compile.compile(ok, doraise=True, quiet=2)
with open(cf, 'rb') as f:
    f.read(16); decomp = marshal.load(f)

def extract(co):
    r = {}; r[co.co_name or '<module>'] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType): r.update(extract(c))
    return r

om = extract(orig); dm = extract(decomp)

co = om['reload_data']
oi = list(dis.get_instructions(co))

print("ORIG around offset 1520-1580:")
for i in oi:
    if 1520 <= i.offset <= 1580:
        a = '%s (%s)' % (i.arg, i.argrepr) if i.arg is not None and i.argrepr else (str(i.arg) if i.arg is not None else '')
        print('  %4d %-35s %s' % (i.offset, i.opname, a))

co2 = dm['reload_data']
di = list(dis.get_instructions(co2))
print()
print("DECOMP around offset 1520-1580:")
for i in di:
    if 1520 <= i.offset <= 1580:
        a = '%s (%s)' % (i.arg, i.argrepr) if i.arg is not None and i.argrepr else (str(i.arg) if i.arg is not None else '')
        print('  %4d %-35s %s' % (i.offset, i.opname, a))
