# Full code-object attribute comparison for CORPUS402-0373 (判定 R7 是否观察层).
import types
orig = r'.trae/specs/attack-completeness-claims/rounds/round9/g2b_402/eqsrc/site-packages__fly__common__user_error__eqsrc.py'
prod = r'.trae/specs/attack-completeness-claims/rounds/round9/g2b_402/semantic_products/CORPUS402-0373.py'

FIELDS = ['co_argcount','co_posonlyargcount','co_kwonlyargcount','co_nlocals',
          'co_stacksize','co_flags','co_firstlineno','co_cellvars','co_freevars']

def sig(code, path='module'):
    d = {path: {f: getattr(code, f) for f in FIELDS}}
    d[path]['co_code_len'] = len(code.co_code)
    d[path]['n_consts'] = len(code.co_consts)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            d.update(sig(c, path + '/' + c.co_name))
    return d

o = sig(compile(open(orig,encoding='utf-8').read(), orig, 'exec'))
p = sig(compile(open(prod,encoding='utf-8').read(), prod, 'exec'))
diffs = 0
for path in dict.fromkeys(list(o)+list(p)):
    if o.get(path) != p.get(path):
        diffs += 1
        print('DIFF', path)
        for f in FIELDS + ['co_code_len','n_consts']:
            ov, pv = (o.get(path) or {}).get(f), (p.get(path) or {}).get(f)
            if ov != pv:
                print(f'   {f}: ORIG={ov!r} PROD={pv!r}')
print('total code-object sig diffs:', diffs)
