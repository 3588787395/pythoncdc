"""R23: analyze return None length differences in detail"""
import sys, os, json, marshal, types, dis
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from pycdc import decompile_pyc

with open(r'f:/Downloads/pythoncdc-main/.trae/specs/region-comment-multi-pyc-iteration/rounds/round_22/batch_results.json', 'r') as f:
    results = json.load(f)

partials = [r for r in results['results'] if r.get('status') == 'partial']

def collect_funcs(code, out):
    out.append(code)
    for c in getattr(code, 'co_consts', []):
        if isinstance(c, types.CodeType):
            collect_funcs(c, out)
    return out

# For +4 diff (orig has extra return None): check if decompiled source
# is missing the implicit return None
# For -4 diff (dec has extra return None): check if decompiled source
# has a spurious explicit return None

orig_longer_4 = 0  # orig +4: missing return None in decompiled
dec_longer_4 = 0   # dec -4: extra return None in decompiled

# Also analyze -26 diff (dec 26 bytes longer)
dec_longer_26_examples = []

for r in partials:
    pyc_path = r['path']
    if not os.path.exists(pyc_path):
        continue
    try:
        src = decompile_pyc(pyc_path)
        compiled = compile(src, '<dec>', 'exec')
    except:
        continue
    
    with open(pyc_path, 'rb') as f:
        f.read(16)
        orig_code = marshal.load(f)
    
    orig_funcs = collect_funcs(orig_code, [])
    dec_funcs = collect_funcs(compiled, [])
    
    for orig, dec in zip(orig_funcs, dec_funcs):
        obytes = orig.co_code
        dbytes = dec.co_code
        if len(obytes) == len(dbytes):
            continue
        
        diff = len(obytes) - len(dbytes)
        
        # Check for return None pattern
        # Python 3.12: RETURN_CONST None (2 bytes)
        # Python 3.11: LOAD_CONST None; RETURN_VALUE (4 bytes)
        if diff == 4:
            orig_longer_4 += 1
        elif diff == -4:
            dec_longer_4 += 1
        elif diff == -26 and len(dec_longer_26_examples) < 5:
            dec_longer_26_examples.append((orig.co_name, os.path.basename(pyc_path), len(obytes), len(dbytes)))

print(f'Orig +4 (missing return None in dec): {orig_longer_4}')
print(f'Dec -4 (extra return None in dec): {dec_longer_4}')
print(f'\nDec -26 examples (dec 26 bytes longer):')
for name, pyc, orig_len, dec_len in dec_longer_26_examples:
    print(f'  {name} in {pyc}: orig={orig_len} dec={dec_len}')
