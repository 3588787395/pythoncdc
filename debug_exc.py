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
entries = list(dis._parse_exception_table(co))
print('ORIG reload_data exception table:')
for e in entries:
    print('  start=%d end=%d depth=%d lasti=%d target=%d' % (e.start, e.end, e.depth, e.lasti, e.target))

co2 = dm['reload_data']
entries2 = list(dis._parse_exception_table(co2))
print()
print('DECOMP reload_data exception table:')
for e in entries2:
    print('  start=%d end=%d depth=%d lasti=%d target=%d' % (e.start, e.end, e.depth, e.lasti, e.target))
