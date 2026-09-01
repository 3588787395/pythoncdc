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

lc_jf_cases = []

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
        
        td = true_diffs[0]
        if td.get('orig_op') == 'LOAD_CONST' and td.get('decomp_op') == 'JUMP_FORWARD':
            lc_jf_cases.append({
                'func': name,
                'file': pyc_path.split('site-packages')[-1],
                'true_diffs': len(true_diffs),
                'orig_arg': td.get('orig_arg'),
                'decomp_arg': td.get('decomp_arg'),
            })

lc_jf_cases.sort(key=lambda x: x['true_diffs'])
print(f"LOAD_CONST -> JUMP_FORWARD cases: {len(lc_jf_cases)}")
for c in lc_jf_cases[:10]:
    print(f"  {c['true_diffs']} diffs: {c['func']} in {c['file']}, orig={c['orig_arg']}, decomp={c['decomp_arg']}")
