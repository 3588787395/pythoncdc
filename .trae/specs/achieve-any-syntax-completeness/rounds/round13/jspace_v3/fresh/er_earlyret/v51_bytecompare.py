# v51-ERGUARD round: byte-compare harness (per-code-object co_code + exceptiontable).
# Usage: python v51_bytecompare.py <orig.pyc> <product.py>
import marshal, os, sys, py_compile

def codemap(c, prefix=''):
    m = {}
    key = prefix + c.co_name
    m[key] = c
    for k in c.co_consts:
        if hasattr(k, 'co_code'):
            m.update(codemap(k, key + '.'))
    return m

orig_pyc, prod_src = sys.argv[1], sys.argv[2]
cpyc = prod_src + '.__cmp__.pyc'
if os.path.exists(cpyc):
    os.remove(cpyc)
py_compile.compile(prod_src, cfile=cpyc, doraise=True)
om = codemap(marshal.loads(open(orig_pyc, 'rb').read()[16:]))
nm = codemap(marshal.loads(open(cpyc, 'rb').read()[16:]))
bad = []
for k in sorted(set(om) | set(nm)):
    if k not in om or k not in nm:
        bad.append((k, 'presence')); continue
    a, b = om[k], nm[k]
    if a.co_code != b.co_code:
        bad.append((k, 'co_code'))
    elif a.co_exceptiontable != b.co_exceptiontable:
        bad.append((k, 'exc'))
print('BYTE-EQUAL' if not bad else 'DIFF ' + str(bad))
sys.exit(0 if not bad else 1)
