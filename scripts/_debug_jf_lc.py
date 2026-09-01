import sys, json, marshal, types, dis
sys.path.insert(0, '.')
from testqouter.round1.base import compare_bytecode, _filter_noise_instrs

with open('pyc_index.json', 'r', encoding='utf-8') as f:
    index = json.load(f)

def get_all_codes(c):
    result = [c]
    for const in c.co_consts:
        if isinstance(const, types.CodeType):
            result.extend(get_all_codes(const))
    return result

jf_lc_cases = []

for entry in index:
    if entry.get('decompile_status') != 'partial':
        continue
    pyc_path = entry['path']
    try:
        with open(pyc_path, 'rb') as f:
            f.read(16)
            code = marshal.load(f)
    except:
        continue
    
    all_codes = get_all_codes(code)
    
    import subprocess
    result = subprocess.run([sys.executable, '-m', 'pycdc', pyc_path], 
                          capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode != 0:
        continue
    
    try:
        decomp_code = compile(result.stdout, '<decompiled>', 'exec')
    except:
        continue
    
    decomp_codes = get_all_codes(decomp_code)
    
    for co in all_codes:
        decomp_co = None
        for dc in decomp_codes:
            if dc.co_name == co.co_name and dc.co_freevars == co.co_freevars and dc.co_cellvars == co.co_cellvars:
                decomp_co = dc
                break
        if decomp_co is None:
            continue
        
        details = compare_bytecode(co, decomp_co)
        if details.get('match', False):
            continue
        
        first_diff = details.get('first_diff', {})
        orig_op = first_diff.get('orig_op')
        decomp_op = first_diff.get('decomp_op')
        
        if orig_op == 'JUMP_FORWARD' and decomp_op == 'LOAD_CONST':
            orig_idx = first_diff.get('orig_idx', 0)
            decomp_idx = first_diff.get('decomp_idx', 0)
            orig_filtered = _filter_noise_instrs(list(dis.get_instructions(co)))
            decomp_filtered = _filter_noise_instrs(list(dis.get_instructions(decomp_co)))
            context_orig = [(i.opname, getattr(i, 'argval', None)) for i in orig_filtered[max(0,orig_idx-3):orig_idx+4]]
            context_decomp = [(i.opname, getattr(i, 'argval', None)) for i in decomp_filtered[max(0,decomp_idx-3):decomp_idx+4]]
            jf_lc_cases.append({
                'file': pyc_path.split('site-packages')[-1] if 'site-packages' in pyc_path else pyc_path,
                'func': co.co_name,
                'orig_idx': orig_idx,
                'decomp_idx': decomp_idx,
                'context_orig': context_orig,
                'context_decomp': context_decomp,
                'total_orig': len(orig_filtered),
                'total_decomp': len(decomp_filtered),
            })

print(f"JUMP_FORWARD -> LOAD_CONST cases: {len(jf_lc_cases)}")
for i, c in enumerate(jf_lc_cases[:15]):
    print(f"\n--- Case {i+1}: {c['func']} in {c['file']} ---")
    print(f"  orig_idx={c['orig_idx']}/{c['total_orig']}, decomp_idx={c['decomp_idx']}/{c['total_decomp']}")
    print(f"  orig context:  {c['context_orig']}")
    print(f"  decomp context: {c['context_decomp']}")
