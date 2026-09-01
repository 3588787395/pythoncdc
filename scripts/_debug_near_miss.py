import sys, json, marshal, types, os, py_compile, importlib.util
sys.path.insert(0, '.')
from testqouter.round1.base import compare_bytecode

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

near_miss = []

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
        n = len(true_diffs)
        if 1 <= n <= 4:
            td0 = true_diffs[0] if true_diffs else {}
            near_miss.append({
                'func': name,
                'file': pyc_path.split('site-packages')[-1],
                'true_diffs': n,
                'first_diff': f"{td0.get('orig_op','?')}({td0.get('orig_arg','')}) -> {td0.get('decomp_op','?')}({td0.get('decomp_arg','')})",
            })

near_miss.sort(key=lambda x: x['true_diffs'])
print(f"Near-miss functions (1-4 true_diffs): {len(near_miss)}")
for c in near_miss[:20]:
    print(f"  {c['true_diffs']} diffs: {c['func']} in {c['file']}, first: {c['first_diff']}")
