import sys, marshal, types, dis
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQData/utils/common_func.pyc'
ok = pyc.replace('.pyc', 'OK.py')
with open(pyc, 'rb') as f:
    f.read(16)
    orig = marshal.load(f)

import py_compile
cf = py_compile.compile(ok, doraise=True, quiet=2)
if cf is None:
    import importlib.util
    cf = importlib.util.cache_from_source(ok)
with open(cf, 'rb') as f:
    f.read(16)
    decomp = marshal.load(f)

def extract(co):
    r = {}
    r[co.co_name or '<module>'] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r.update(extract(c))
    return r

om = extract(orig)
dm = extract(decomp)

name = 'handle_exrights'
print('=== ORIGINAL (first 30) ===')
for i in list(dis.get_instructions(om[name]))[:30]:
    a = f'{i.arg} ({i.argrepr})' if i.arg is not None and i.argrepr else (str(i.arg) if i.arg is not None else '')
    print(f'  {i.offset:4d} {i.opname:35s} {a}')

print()
print('=== DECOMPILED (first 30) ===')
for i in list(dis.get_instructions(dm[name]))[:30]:
    a = f'{i.arg} ({i.argrepr})' if i.arg is not None and i.argrepr else (str(i.arg) if i.arg is not None else '')
    print(f'  {i.offset:4d} {i.opname:35s} {a}')

print()
print('=== SOURCE ===')
with open(ok, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()
lines = content.split('\n')
in_f = False
fl = []
for l in lines:
    s = l.strip()
    if 'def handle_exrights' in s:
        in_f = True
        fl.append(l)
        continue
    if in_f:
        ci = len(l) - len(l.lstrip()) if l.strip() else 999
        di = len(fl[0]) - len(fl[0].lstrip()) if fl else 0
        if s and ci <= di and fl:
            break
        fl.append(l)
for l in fl[:30]:
    print(l)
