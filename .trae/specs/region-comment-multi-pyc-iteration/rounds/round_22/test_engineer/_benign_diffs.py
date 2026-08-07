"""R22: classify bytecode differences as benign vs real"""
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

benign_count = 0
real_diff_count = 0
len_diff_count = 0
total_unmatched = 0

for r in partials:
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
        
        total_unmatched += 1
        obytes = orig.co_code
        dbytes = dec.co_code
        
        if len(obytes) != len(dbytes):
            len_diff_count += 1
            continue
        
        all_benign = True
        for i in range(0, len(obytes), 2):
            if obytes[i] != dbytes[i] or obytes[i+1] != dbytes[i+1]:
                op_o = dis.opname[obytes[i]] if obytes[i] < len(dis.opname) else 'UNK'
                if obytes[i] == dbytes[i] and op_o == 'LOAD_CONST':
                    arg_o = obytes[i+1]
                    arg_d = dbytes[i+1]
                    val_o = orig.co_consts[arg_o] if arg_o < len(orig.co_consts) else None
                    val_d = dec.co_consts[arg_d] if arg_d < len(dec.co_consts) else None
                    if val_o == val_d:
                        continue  # benign: same value, different pool index
                all_benign = False
                break
        
        if all_benign:
            benign_count += 1
        else:
            real_diff_count += 1

print(f'Total unmatched: {total_unmatched}')
print(f'Benign (LOAD_CONST pool order only): {benign_count}')
print(f'Length difference: {len_diff_count}')
print(f'Real opcode difference: {real_diff_count}')
print(f'\nIf benign are treated as match:')
new_match = total_unmatched - benign_count
print(f'  Effective unmatched: {new_match}')
