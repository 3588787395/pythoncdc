import sys, marshal, types, dis
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from testqouter.round1.base import compare_bytecode

pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc'
ok = pyc.replace('.pyc', 'OK.py')
with open(pyc, 'rb') as f:
    f.read(16); orig = marshal.load(f)
import py_compile
cf = py_compile.compile(ok, doraise=True, quiet=2)
if cf is None:
    import importlib.util
    cf = importlib.util.cache_from_source(ok)
with open(cf, 'rb') as f:
    f.read(16); decomp = marshal.load(f)

def extract(co):
    r = {}; r[co.co_name or '<module>'] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType): r.update(extract(c))
    return r

om = extract(orig); dm = extract(decomp)
co_o = om['match']
co_d = dm['match']
oi = list(dis.get_instructions(co_o))
di = list(dis.get_instructions(co_d))

# Find where orig has the SELL check (around offset 1194)
print("=== ORIG around 1194-1320 ===")
for i in oi:
    if 1190 <= i.offset <= 1330:
        a = f'{i.arg} ({i.argrepr})' if i.arg is not None and i.argrepr else (str(i.arg) if i.arg is not None else '')
        print(f'  {i.offset:4d} {i.opname:35s} {a}')

print("\n=== DECOMP around 1196-1330 ===")
for i in di:
    if 1190 <= i.offset <= 1330:
        a = f'{i.arg} ({i.argrepr})' if i.arg is not None and i.argrepr else (str(i.arg) if i.arg is not None else '')
        print(f'  {i.offset:4d} {i.opname:35s} {a}')

# Print the full sections that differ
print("\n=== FULL ORIG ===")
for i in oi:
    a = f'{i.arg} ({i.argrepr})' if i.arg is not None and i.argrepr else (str(i.arg) if i.arg is not None else '')
    print(f'  {i.offset:4d} {i.opname:35s} {a}')

print("\n=== FULL DECOMP ===")
for i in di:
    a = f'{i.arg} ({i.argrepr})' if i.arg is not None and i.argrepr else (str(i.arg) if i.arg is not None else '')
    print(f'  {i.offset:4d} {i.opname:35s} {a}')
