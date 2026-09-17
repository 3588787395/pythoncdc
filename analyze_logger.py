import sys, marshal, types, dis
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from testqouter.round1.base import compare_bytecode

pyc = 'F:/Downloads/pythoncdc-main/site-packages/fly/logger.pyc'
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

for name in ['write_logging_thread', 'logging_process']:
    cmp = compare_bytecode(om[name], dm[name])
    td = cmp.get('true_diffs', [])
    print('=== %s ===' % name)
    print('orig=%d decomp=%d jd=%d td=%d' % (cmp.get('orig_count'), cmp.get('decomp_count'), len(cmp.get('jump_diffs',[])), len(td)))
    for t in td: print('  ', t)

    oi = list(dis.get_instructions(om[name]))
    di = list(dis.get_instructions(dm[name]))

    print('\nORIG FULL:')
    for i, inst in enumerate(oi):
        a = '%s (%s)' % (inst.arg, inst.argrepr) if inst.arg is not None and inst.argrepr else (str(inst.arg) if inst.arg is not None else '')
        print('  [%3d] %4d %-35s %s' % (i, inst.offset, inst.opname, a))
    print('\nDECOMP FULL:')
    for i, inst in enumerate(di):
        a = '%s (%s)' % (inst.arg, inst.argrepr) if inst.arg is not None and inst.argrepr else (str(inst.arg) if inst.arg is not None else '')
        print('  [%3d] %4d %-35s %s' % (i, inst.offset, inst.opname, a))
    print()
