import sys, marshal, types, dis
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from testqouter.round1.base import compare_bytecode

def extract(co):
    r = {}; r[co.co_name or '<module>'] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType): r.update(extract(c))
    return r

def analyze(pyc_path, func_name=None):
    ok_path = pyc_path.replace('.pyc', 'OK.py')
    with open(pyc_path, 'rb') as f:
        f.read(16); orig = marshal.load(f)
    import py_compile
    cf = py_compile.compile(ok_path, doraise=True, quiet=2)
    if cf is None:
        import importlib.util
        cf = importlib.util.cache_from_source(ok_path)
    with open(cf, 'rb') as f:
        f.read(16); decomp = marshal.load(f)

    om = extract(orig); dm = extract(decomp)
    for name in sorted(set(om.keys()) & set(dm.keys())):
        if func_name and name != func_name:
            continue
        cmp = compare_bytecode(om[name], dm[name])
        print(f'\n=== {name} === match={cmp.get("match")} jump_only={cmp.get("jump_only")}')
        if not cmp.get('match'):
            td = cmp.get('true_diffs', [])
            jd = cmp.get('jump_diffs', [])
            print(f'orig={cmp.get("orig_count")} decomp={cmp.get("decomp_count")} jd={len(jd)} td={len(td)}')
            for t in td[:12]: print(f'  {t}')

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'finance'
    func = sys.argv[2] if len(sys.argv) > 2 else None
    if target == 'strategy':
        analyze('F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc', func)
    else:
        analyze('F:/Downloads/pythoncdc-main/site-packages/IQData/plugins/plugin_system_local_finance/finance_data_source.pyc', func)
