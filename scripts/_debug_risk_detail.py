import sys, json, marshal, types, py_compile
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

for entry in json.load(open('pyc_index.json', 'r', encoding='utf-8')):
    if 'risk_calculation' not in entry.get('path', ''):
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
    common = sorted(set(orig_map.keys()) & set(decomp_map.keys()))
    total = len(common)
    matched = 0
    for name in common:
        details = compare_bytecode(orig_map[name], decomp_map[name])
        if details.get('match') or details.get('jump_only'):
            matched += 1
        else:
            td = details.get('true_diffs', [])
            if len(td) <= 10:
                print("UNMATCHED: %s (%d true_diffs)" % (name.split('.')[-1], len(td)))
    print("Total: %d, Matched: %d, Rate: %.2f%%" % (total, matched, matched/total*100 if total else 0))
    break
