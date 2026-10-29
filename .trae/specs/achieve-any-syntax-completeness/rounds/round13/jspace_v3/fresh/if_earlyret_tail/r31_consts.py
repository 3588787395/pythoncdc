# Find which nested code objects lose consts in REAL46-031 (original pyc vs product).
import sys, types, dis
ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)
import json, os

pyc = os.path.join(ROOT, r'.trae/specs/attack-completeness-claims/rounds/round9/g2c_46/pyc')
# locate REAL46-031 pyc from space
space = json.load(open(os.path.join(ROOT, r'.trae/specs/attack-completeness-claims/rounds/round9/g2c_46/space_46.json'), encoding='utf-8'))
entry = {e['id']: e for e in space['entries'] if isinstance(e, dict)}['REAL46-031']
orig_pyc = os.path.join(ROOT, entry['pyc'])

with open(orig_pyc, 'rb') as f:
    f.read(16)  # header
    import marshal
    orig_code = marshal.load(f)

prod_path = r'D:\temp\opencode\g2c_r5_products\REAL46-031.py'
prod_code = compile(open(prod_path, encoding='utf-8').read(), prod_path, 'exec')

def tree(code, path='module'):
    out = {path: code}
    for i, c in enumerate(code.co_consts):
        if isinstance(c, types.CodeType):
            out.update(tree(c, f'{path}/{c.co_name}#{i}'))
    return out

ot, pt = tree(orig_code), tree(prod_code)
print('orig code objects', len(ot), 'prod code objects', len(pt))
common = [p for p in ot if p in pt]
print('common paths', len(common))
for p in common:
    oc, pc = ot[p], pt[p]
    if len(oc.co_consts) != len(pc.co_consts):
        print('='*60)
        print(f'{p}: consts {len(oc.co_consts)} -> {len(pc.co_consts)}')
        # show consts by type/name
        def brief(c):
            if isinstance(c, types.CodeType):
                return f'CODE({c.co_name})'
            return repr(c)[:80]
        oset = [brief(c) for c in oc.co_consts]
        pset = [brief(c) for c in pc.co_consts]
        from collections import Counter
        co, cp = Counter(oset), Counter(pset)
        for k in co:
            if co[k] != cp.get(k, 0):
                print(f'   ORIG x{co[k]} vs PROD x{cp.get(k,0)}: {k}')
        for k in cp:
            if k not in co:
                print(f'   PROD-ONLY x{cp[k]}: {k}')
