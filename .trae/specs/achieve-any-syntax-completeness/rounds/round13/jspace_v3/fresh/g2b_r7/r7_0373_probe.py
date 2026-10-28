# Find the exact R7 metadata diff for CORPUS402-0373 (user_error).
import sys, json, subprocess, types
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')

orig = r'.trae/specs/attack-completeness-claims/rounds/round9/g2b_402/eqsrc/site-packages__fly__common__user_error__eqsrc.py'
prod = r'.trae/specs/attack-completeness-claims/rounds/round9/g2b_402/semantic_products/CORPUS402-0373.py'

def consts_tree(code, depth=0, path='module'):
    out = []
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            out.append((path, 'CODE', c.co_name))
            out.extend(consts_tree(c, depth+1, path + '/' + c.co_name))
        else:
            out.append((path, type(c).__name__, repr(c)[:90]))
    return out

for label, p in (('ORIG', orig), ('PROD', prod)):
    try:
        src = open(p, encoding='utf-8').read()
    except FileNotFoundError:
        print(label, 'MISSING', p); continue
    try:
        code = compile(src, p, 'exec')
    except SyntaxError as e:
        print(label, 'SYNTAX', e.lineno, e.msg); continue
    print('='*30, label, '='*30)
    for path, t, val in consts_tree(code):
        # only print non-numeric-simple consts to focus on strings
        if t in ('str',):
            print(f'  {path:40} {t:6} {val}')
