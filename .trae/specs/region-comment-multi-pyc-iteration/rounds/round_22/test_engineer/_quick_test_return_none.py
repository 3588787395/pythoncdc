"""R23: quick test after return None fix"""
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

match_count = 0
total_count = 0

for r in partials[:10]:
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
        total_count += 1
        if orig.co_code == dec.co_code:
            match_count += 1

print(f'Quick test: {match_count}/{total_count} match ({match_count/total_count*100:.1f}%)')
