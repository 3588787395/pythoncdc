"""R23: analyze bytecode length differences"""
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

len_patterns = {}

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
        if diff not in len_patterns:
            len_patterns[diff] = 0
        len_patterns[diff] += 1

print('Length difference patterns (orig - dec):')
for diff, count in sorted(len_patterns.items(), key=lambda x: -x[1])[:15]:
    direction = 'orig longer' if diff > 0 else 'dec longer'
    print(f'  diff={diff:+5d} ({direction}): {count}x')
