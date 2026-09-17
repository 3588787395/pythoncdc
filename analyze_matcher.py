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
for name in sorted(set(om.keys()) & set(dm.keys())):
    cmp = compare_bytecode(om[name], dm[name])
    if not cmp.get('match') and not cmp.get('jump_only'):
        print(f'\n=== {name} ===')
        td = cmp.get('true_diffs', [])
        print(f'orig={cmp.get("orig_count")} decomp={cmp.get("decomp_count")} jd={len(cmp.get("jump_diffs",[]))} td={len(td)}')
        for t in td[:15]: print(f'  {t}')
        oi = list(dis.get_instructions(om[name]))
        di = list(dis.get_instructions(dm[name]))
        if td:
            idx = td[0].get('index', 0)
            print(f'\nORIG (around idx {idx}):')
            for i in oi[max(0,idx-10):idx+30]:
                a = f'{i.arg} ({i.argrepr})' if i.arg is not None and i.argrepr else (str(i.arg) if i.arg is not None else '')
                print(f'  {i.offset:4d} {i.opname:35s} {a}')
            print(f'\nDECOMP (around idx {idx}):')
            for i in di[max(0,idx-10):idx+30]:
                a = f'{i.arg} ({i.argrepr})' if i.arg is not None and i.argrepr else (str(i.arg) if i.arg is not None else '')
                print(f'  {i.offset:4d} {i.opname:35s} {a}')
