import sys, json, marshal, types, os, py_compile, importlib.util
sys.path.insert(0, '.')
from testqouter.round1.base import compare_bytecode, _filter_noise_instrs, get_bytecode_instructions

def _load_pyc_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def _extract_code_objects(code, prefix=''):
    result = {}
    key = prefix + code.co_name
    result[key] = code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(_extract_code_objects(const, prefix + code.co_name + '.'))
    return result

with open('pyc_index.json', 'r', encoding='utf-8') as f:
    index = json.load(f)

# Count how many diffs are just jump direction inversions (PJIF_TRUE <-> PJIF_FALSE)
# with the same target at the same position
jump_inversion_count = 0
jump_inversion_funcs = []

for entry in index:
    if entry.get('decompile_status') != 'partial':
        continue
    pyc_path = entry['path']
    ok_py_path = pyc_path[:-4] + 'OK.py'
    
    try:
        orig_code = _load_pyc_code(pyc_path)
    except:
        continue
    
    if not os.path.exists(ok_py_path):
        continue
    
    try:
        cfile = py_compile.compile(ok_py_path, doraise=True, quiet=2)
        if cfile is None:
            cfile = importlib.util.cache_from_source(ok_py_path)
        with open(cfile, 'rb') as f:
            f.read(16)
            decomp_code = marshal.load(f)
    except:
        continue
    
    orig_map = _extract_code_objects(orig_code)
    decomp_map = _extract_code_objects(decomp_code)
    
    common = set(orig_map.keys()) & set(decomp_map.keys())
    for name in sorted(common):
        details = compare_bytecode(orig_map[name], decomp_map[name])
        if details.get('match') or details.get('jump_only'):
            continue
        true_diffs = details.get('true_diffs', [])
        if not true_diffs:
            continue
        
        for td in true_diffs:
            o = td.get('orig_op', '')
            d = td.get('decomp_op', '')
            if (o.startswith('POP_JUMP_') and d.startswith('POP_JUMP_') and
                '_IF_TRUE' in o and '_IF_FALSE' in d):
                jump_inversion_count += 1
                if len(jump_inversion_funcs) < 10:
                    jump_inversion_funcs.append(f"{name} in {pyc_path.split('site-packages')[-1]}")

print(f"Jump direction inversion diffs (PJIF_TRUE <-> PJIF_FALSE): {jump_inversion_count}")
for f in jump_inversion_funcs:
    print(f"  {f}")
