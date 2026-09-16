import sys, marshal, types, dis
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from testqouter.round1.base import compare_bytecode

pyc = 'F:/Downloads/pythoncdc-main/site-packages/fly/oauthenticator/oauth2.pyc'
ok_path = pyc.replace('.pyc', 'OK.py')
with open(pyc, 'rb') as f:
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
    if not cmp.get('match'):
        print('=== %s ===' % name)
        print('orig=%d decomp=%d td=%d' % (cmp.get('orig_count',0), cmp.get('decomp_count',0), len(cmp.get('true_diffs',[]))))
        td = cmp.get('true_diffs', [])
        for t in td[:5]: print('  td: %s' % (t,))
