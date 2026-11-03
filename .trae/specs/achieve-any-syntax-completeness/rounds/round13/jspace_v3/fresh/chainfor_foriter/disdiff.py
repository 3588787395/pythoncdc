import dis, marshal, types, py_compile, sys, itertools
def load(p):
    with open(p,'rb') as f: return marshal.loads(f.read()[16:])
a = load('D:/Python/Lib/__pycache__/dataclasses.cpython-311.pyc')
py_compile.compile('dc_prod_v108.py', 'dc_prod.pyc', doraise=True)
b = load('dc_prod.pyc')
fa = {}; fb = {}
def flat(c, out, prefix=''):
    out[prefix + c.co_name] = c
    for k in c.co_consts:
        if isinstance(k, types.CodeType): flat(k, out, prefix + c.co_name + '.')
flat(a, fa); flat(b, fb)
name = sys.argv[1]
ca, cb = fa['<module>.' + name], fb['<module>.' + name]
ia = list(dis.get_instructions(ca)); ib = list(dis.get_instructions(cb))
print('%s: orig %d bytes, prod %d bytes' % (name, len(ca.co_code), len(cb.co_code)))
# align by offset windows; find first divergence
i = j = 0
ndiv = 0
while i < len(ia) and j < len(ib) and ndiv < 3:
    x, y = ia[i], ib[j]
    if x.opname == y.opname and x.arg == y.arg:
        i += 1; j += 1; continue
    print('DIVERGE at A@%d(%s %s) vs B@%d(%s %s)' % (x.offset, x.opname, x.argrepr[:30], y.offset, y.opname, y.argrepr[:30]))
    print('  A ctx:', ' | '.join('%s %s' % (w.opname, w.argrepr[:22]) for w in ia[max(0,i-3):i+6]))
    print('  B ctx:', ' | '.join('%s %s' % (w.opname, w.argrepr[:22]) for w in ib[max(0,j-3):j+6]))
    ndiv += 1
    # naive resync: try to find y in next 20 A instrs or x in next 20 B instrs
    resync = False
    for di in range(0, 20):
        for dj in range(0, 20):
            if i+di < len(ia) and j+dj < len(ib) and ia[i+di].opname == ib[j+dj].opname and ia[i+di].arg == ib[j+dj].arg:
                aa = ia[i+di]; bb = ib[j+dj]
                # require 4 consecutive matches to resync
                ok = all(ia[i+di+t].opname == ib[j+dj+t].opname and ia[i+di+t].arg == ib[j+dj+t].arg for t in range(4) if i+di+t < len(ia) and j+dj+t < len(ib))
                if ok and di + dj < 25:
                    i += di; j += dj; resync = True; break
        if resync: break
    if not resync: break
