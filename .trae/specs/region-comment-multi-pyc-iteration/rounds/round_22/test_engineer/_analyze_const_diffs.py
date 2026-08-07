"""R22: analyze LOAD_CONST value differences"""
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

const_diff_examples = []

for r in partials[:50]:
    pyc_path = r['path']
    if not os.path.exists(pyc_path):
        continue
    try:
        dec_src = decompile_pyc(pyc_path)
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
        
        obytes = orig.co_code
        dbytes = dec.co_code
        
        for i in range(0, min(len(obytes), len(dbytes)), 2):
            if obytes[i] != dbytes[i]:
                op_o = dis.opname[obytes[i]] if obytes[i] < len(dis.opname) else 'UNK'
                op_d = dis.opname[dbytes[i]] if dbytes[i] < len(dis.opname) else 'UNK'
                if op_o == 'LOAD_CONST' and op_d == 'LOAD_CONST':
                    arg_o = obytes[i+1]
                    arg_d = dbytes[i+1]
                    val_o = orig.co_consts[arg_o] if arg_o < len(orig.co_consts) else '?'
                    val_d = dec.co_consts[arg_d] if arg_d < len(dec.co_consts) else '?'
                    if len(const_diff_examples) < 30:
                        const_diff_examples.append((orig.co_name, val_o, val_d))
                break

print(f'LOAD_CONST value differences ({len(const_diff_examples)} examples):')
val_patterns = {}
for name, val_o, val_d in const_diff_examples:
    key = f'{repr(val_o)} -> {repr(val_d)}'
    if key not in val_patterns:
        val_patterns[key] = []
    val_patterns[key].append(name)

for pattern, names in sorted(val_patterns.items(), key=lambda x: -len(x[1])):
    print(f'  {len(names):3d}x {pattern}')
    for n in names[:2]:
        print(f'       in {n}')
