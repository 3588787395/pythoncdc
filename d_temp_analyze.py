import sys, marshal, types, dis
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from testqouter.round1.base import compare_bytecode

def analyze(pyc_path):
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
    def extract(co):
        r = {}; r[co.co_name or '<module>'] = co
        for c in co.co_consts:
            if isinstance(c, types.CodeType): r.update(extract(c))
        return r
    om = extract(orig); dm = extract(decomp)
    for name in sorted(set(om.keys()) & set(dm.keys())):
        cmp = compare_bytecode(om[name], dm[name])
        if not cmp.get('match') and not cmp.get('jump_only'):
            print('\n=== %s ===' % name)
            print('orig=%d decomp=%d jd=%d td=%d' % (cmp.get('orig_count',0), cmp.get('decomp_count',0), len(cmp.get('jump_diffs',[])), len(cmp.get('true_diffs',[]))))
            td = cmp.get('true_diffs', [])
            for t in td[:10]: print('  td: %s' % (t,))
            print('\nORIG bytecode:')
            for i in list(dis.get_instructions(om[name]))[:80]:
                a = '%d (%s)' % (i.arg, i.argrepr) if i.arg is not None and i.argrepr else (str(i.arg) if i.arg is not None else '')
                print('  %4d %-35s %s' % (i.offset, i.opname, a))
            print('\nDECOMP bytecode:')
            for i in list(dis.get_instructions(dm[name]))[:80]:
                a = '%d (%s)' % (i.arg, i.argrepr) if i.arg is not None and i.argrepr else (str(i.arg) if i.arg is not None else '')
                print('  %4d %-35s %s' % (i.offset, i.opname, a))

if len(sys.argv) > 1:
    analyze(sys.argv[1])
else:
    analyze('F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_persist/__init__.pyc')
