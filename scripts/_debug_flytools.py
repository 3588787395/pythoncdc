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

# Check flytools.pyc (63 funcs in index, 62 matched)
with open('pyc_index.json', 'r', encoding='utf-8') as f:
    index = json.load(f)

for entry in index:
    if 'flytools' not in entry.get('path', ''):
        continue
    pyc_path = entry['path']
    ok_py_path = pyc_path[:-4] + 'OK.py'
    
    orig_code = _load_pyc_code(pyc_path)
    cfile = py_compile.compile(ok_py_path, doraise=True, quiet=2)
    with open(cfile, 'rb') as f:
        f.read(16)
        decomp_code = marshal.load(f)
    
    orig_map = _extract_code_objects(orig_code)
    decomp_map = _extract_code_objects(decomp_code)
    
    common = set(orig_map.keys()) & set(decomp_map.keys())
    for name in sorted(common):
        details = compare_bytecode(orig_map[name], decomp_map[name])
        if not details.get('match') and not details.get('jump_only'):
            true_diffs = details.get('true_diffs', [])
            print(f"MISMATCH: {name}")
            for td in true_diffs[:5]:
                print(f"  idx={td['index']}: orig={td.get('orig_op','')}({td.get('orig_arg','')}) decomp={td.get('decomp_op','')}({td.get('decomp_arg','')})")
    
    # Check for functions in orig but not in decomp
    orig_only = set(orig_map.keys()) - set(decomp_map.keys())
    for name in sorted(orig_only):
        print(f"ORIG_ONLY: {name}")
    
    decomp_only = set(decomp_map.keys()) - set(orig_map.keys())
    for name in sorted(decomp_only):
        print(f"DECOMP_ONLY: {name}")
    break
