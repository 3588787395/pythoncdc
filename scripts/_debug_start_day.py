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
    if 'tradingday_calendar' not in entry.get('path', ''):
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
    for name in sorted(set(orig_map.keys()) & set(decomp_map.keys())):
        if 'get_start_day' not in name:
            continue
        details = compare_bytecode(orig_map[name], decomp_map[name])
        print("match=%s jump_only=%s true_diffs=%d" % (
            details.get('match'), details.get('jump_only'), len(details.get('true_diffs', []))))
        for td in details.get('true_diffs', []):
            print("  idx=%d: orig=%s(%s) decomp=%s(%s)" % (
                td['index'], td.get('orig_op',''), td.get('orig_arg',''),
                td.get('decomp_op',''), td.get('decomp_arg','')))
    break
