"""R22: analyze bytecode difference patterns"""
import sys, os, json, marshal, types, dis
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from pycdc import decompile_pyc

with open(r'f:/Downloads/pythoncdc-main/.trae/specs/region-comment-multi-pyc-iteration/rounds/round_22/batch_results.json', 'r') as f:
    results = json.load(f)

partials = [r for r in results['results'] if r.get('status') == 'partial']

pattern_counts = {}
total_analyzed = 0
total_unmatched = 0

def collect_funcs(code, out):
    out.append(code)
    for c in getattr(code, 'co_consts', []):
        if isinstance(c, types.CodeType):
            collect_funcs(c, out)
    return out

for r in partials[:30]:
    pyc_path = r['path']
    if not os.path.exists(pyc_path):
        continue
    
    try:
        dec_src = decompile_pyc(pyc_path)
    except:
        continue
    
    try:
        compiled = compile(dec_src, '<dec>', 'exec')
    except:
        continue
    
    with open(pyc_path, 'rb') as f:
        f.read(16)
        orig_code = marshal.load(f)
    
    orig_funcs = collect_funcs(orig_code, [])
    dec_funcs = collect_funcs(compiled, [])
    
    for orig, dec in zip(orig_funcs, dec_funcs):
        if orig.co_code == dec.co_code:
            continue
        
        total_unmatched += 1
        if total_unmatched > 200:
            break
        
        orig_bytes = orig.co_code
        dec_bytes = dec.co_code
        
        if len(orig_bytes) != len(dec_bytes):
            pattern = f'len_diff({len(orig_bytes)}vs{len(dec_bytes)})'
        else:
            diffs = []
            for i in range(0, min(len(orig_bytes), len(dec_bytes)), 2):
                if i >= len(dec_bytes):
                    break
                if orig_bytes[i] != dec_bytes[i] or (i+1 < len(orig_bytes) and i+1 < len(dec_bytes) and orig_bytes[i+1] != dec_bytes[i+1]):
                    op_orig = dis.opname[orig_bytes[i]] if orig_bytes[i] < len(dis.opname) else f'UNK_{orig_bytes[i]}'
                    op_dec = dis.opname[dec_bytes[i]] if dec_bytes[i] < len(dis.opname) else f'UNK_{dec_bytes[i]}'
                    diffs.append(f'{op_orig}->{op_dec}')
            if len(diffs) <= 3:
                pattern = ','.join(diffs)
            else:
                pattern = f'{len(diffs)}_op_diffs_first:{diffs[0]}'
        
        if pattern not in pattern_counts:
            pattern_counts[pattern] = 0
        pattern_counts[pattern] += 1
        total_analyzed += 1
    
    if total_unmatched > 200:
        break

print(f'Analyzed {total_analyzed} unmatched functions')
print(f'\nTop bytecode difference patterns:')
for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1])[:20]:
    print(f'  {count:4d}x {pattern[:80]}')
