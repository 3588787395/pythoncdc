import sys
sys.path.insert(0, '.')
from testqouter.round1.base import compare_bytecode
import marshal, types, py_compile

def load_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def extract_all_funcs(code, prefix=''):
    result = {}
    key = prefix + code.co_name
    result[key] = code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_all_funcs(const, prefix + code.co_name + '.'))
    return result

orig_code = load_code('site-packages/IQEngine/utils/__init__.pyc')
cfile = py_compile.compile('site-packages/IQEngine/utils/__init__OK.py', doraise=True, quiet=2)
with open(cfile, 'rb') as f:
    f.read(16)
    decomp_code = marshal.load(f)

orig_map = extract_all_funcs(orig_code)
decomp_map = extract_all_funcs(decomp_code)

for name in sorted(set(orig_map.keys()) & set(decomp_map.keys())):
    details = compare_bytecode(orig_map[name], decomp_map[name])
    if not details.get('match') and not details.get('jump_only'):
        true_diffs = details.get('true_diffs', [])
        if true_diffs:
            print(f"{name}: {len(true_diffs)} true_diffs")
            for td in true_diffs[:5]:
                print(f"  idx={td['index']}: orig={td.get('orig_op','')}({td.get('orig_arg','')}) decomp={td.get('decomp_op','')}({td.get('decomp_arg','')})")
