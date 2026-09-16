import sys, marshal, types, dis, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from testqouter.round1.base import compare_bytecode

pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc'
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
for name in sorted(set(om.keys()) & set(dm.keys())):
    cmp = compare_bytecode(om[name], dm[name])
    match = cmp.get('match')
    jo = cmp.get('jump_only')
    if not match and not jo:
        print(f'\n=== {name} ===')
        td = cmp.get('true_diffs', [])
        print(f'orig={cmp.get("orig_count")} decomp={cmp.get("decomp_count")} jd={len(cmp.get("jump_diffs",[]))} td={len(td)}')
        for t in td[:5]: print(f'  {t}')
        print('ORIG:')
        for i in list(dis.get_instructions(om[name])):
            a = f'{i.arg} ({i.argrepr})' if i.arg is not None and i.argrepr else (str(i.arg) if i.arg is not None else '')
            print(f'  {i.offset:4d} {i.opname:35s} {a}')
        print('DECOMP:')
        for i in list(dis.get_instructions(dm[name])):
            a = f'{i.arg} ({i.argrepr})' if i.arg is not None and i.argrepr else (str(i.arg) if i.arg is not None else '')
            print(f'  {i.offset:4d} {i.opname:35s} {a}')
