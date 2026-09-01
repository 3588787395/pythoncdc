import sys, json, marshal, types, py_compile
sys.path.insert(0, '.')
from testqouter.round1.base import compare_bytecode

def load_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def extract_all(code, prefix=''):
    result = {}
    key = prefix + code.co_name
    result[key] = code
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            result.update(extract_all(c, prefix + code.co_name + '.'))
    return result

with open('pyc_index.json', 'r', encoding='utf-8') as f:
    index = json.load(f)

for entry in index:
    if 'cgroup_utils' not in entry.get('path', ''):
        continue
    pyc_path = entry['path']
    ok_py_path = pyc_path[:-4] + 'OK.py'
    orig_code = load_code(pyc_path)
    cfile = py_compile.compile(ok_py_path, doraise=True, quiet=2)
    with open(cfile, 'rb') as f:
        f.read(16)
        decomp_code = marshal.load(f)
    orig_map = extract_all(orig_code)
    decomp_map = extract_all(decomp_code)
    common = set(orig_map.keys()) & set(decomp_map.keys())
    for name in sorted(common):
        details = compare_bytecode(orig_map[name], decomp_map[name])
        if not details.get('match') and not details.get('jump_only'):
            td = details.get('true_diffs', [])
            print('MISMATCH: %s, %d true_diffs' % (name, len(td)))
            for t in td[:5]:
                idx = t['index']
                oo = t.get('orig_op', '')
                oa = t.get('orig_arg', '')
                do = t.get('decomp_op', '')
                da = t.get('decomp_arg', '')
                print('  idx=%d: orig=%s(%s) decomp=%s(%s)' % (idx, oo, oa, do, da))
    break
