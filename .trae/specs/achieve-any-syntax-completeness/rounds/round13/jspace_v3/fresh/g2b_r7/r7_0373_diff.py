# Precise const-tree diff for CORPUS402-0373.
import sys, types
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
orig = r'.trae/specs/attack-completeness-claims/rounds/round9/g2b_402/eqsrc/site-packages__fly__common__user_error__eqsrc.py'
prod = r'.trae/specs/attack-completeness-claims/rounds/round9/g2b_402/semantic_products/CORPUS402-0373.py'

def tree(code, path='module'):
    out = []
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            out.append((path, 'CODE:'+c.co_name))
            out.extend(tree(c, path + '/' + c.co_name))
        else:
            out.append((path, repr(c)))
    return out

def names(code, path='module'):
    out = [(path, 'varnames', code.co_varnames), (path, 'names', code.co_names)]
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            out.extend(names(c, path + '/' + c.co_name))
    return out

o = tree(compile(open(orig,encoding='utf-8').read(), orig, 'exec'))
p = tree(compile(open(prod,encoding='utf-8').read(), prod, 'exec'))
print('ORIG const count', len(o), 'PROD const count', len(p))
# align by path, compare per-function
from collections import defaultdict
def bypath(lst):
    d = defaultdict(list)
    for path, v in lst: d[path].append(v)
    return d
ob, pb = bypath(o), bypath(p)
allpaths = list(dict.fromkeys(list(ob.keys()) + list(pb.keys())))
for path in allpaths:
    ov, pv = ob.get(path, []), pb.get(path, [])
    if ov != pv:
        print('='*20, 'DIFF at', path)
        print('  ORIG:', ov)
        print('  PROD:', pv)

print()
print('=== name/varname diff ===')
on = {k:v for k,_,v in names(compile(open(orig,encoding='utf-8').read(), orig, 'exec'))}
# simpler: compare per function
def namepairs(code, path='module'):
    d = {path: (code.co_varnames, code.co_names)}
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            d.update(namepairs(c, path + '/' + c.co_name))
    return d
on = namepairs(compile(open(orig,encoding='utf-8').read(), orig, 'exec'))
pn = namepairs(compile(open(prod,encoding='utf-8').read(), prod, 'exec'))
for path in dict.fromkeys(list(on.keys())+list(pn.keys())):
    if on.get(path) != pn.get(path):
        print('DIFF names', path)
        print('  ORIG varnames/names:', on.get(path))
        print('  PROD varnames/names:', pn.get(path))
