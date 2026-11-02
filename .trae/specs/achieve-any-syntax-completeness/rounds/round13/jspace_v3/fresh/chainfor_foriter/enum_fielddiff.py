import sys, marshal, types
def flat(c, prefix=''):
    out = {}
    name = prefix + c.co_name
    out[name] = c
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            out.update(flat(k, name + '.'))
    return out
def load(pyc):
    with open(pyc, 'rb') as f:
        return marshal.loads(f.read()[16:])
pyc_a, py_b = sys.argv[1], sys.argv[2]
import py_compile
py_compile.compile(py_b, 'field_cmp.pyc', doraise=True)
ca = flat(load(pyc_a)); cb = flat(load('field_cmp.pyc'))
FIELDS = ['co_code','co_exceptiontable','co_names','co_varnames','co_freevars','co_cellvars','co_argcount','co_flags','co_consts','co_firstlineno','co_stacksize']
for k in sorted(set(ca) & set(cb)):
    a, b = ca[k], cb[k]
    ds = []
    for f in FIELDS:
        av, bv = getattr(a, f), getattr(b, f)
        if f == 'co_code': av, bv = av.hex(), bv.hex()
        if f == 'co_exceptiontable': av, bv = av.hex(), bv.hex()
        if f == 'co_consts':
            av = tuple(repr(x) for x in av); bv = tuple(repr(x) for x in bv)
        if av != bv:
            ds.append(f)
    if ds:
        print(k, ':', ','.join(ds))
