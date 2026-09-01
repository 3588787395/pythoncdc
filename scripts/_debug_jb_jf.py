import sys, marshal, types, dis, os, py_compile, importlib.util
sys.path.insert(0, '.')
from testqouter.round1.base import compare_bytecode, _filter_noise_instrs

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

pyc_path = 'site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc'
ok_py_path = pyc_path[:-4] + 'OK.py'

orig_code = _load_pyc_code(pyc_path)
cfile = py_compile.compile(ok_py_path, doraise=True, quiet=2)
if cfile is None:
    cfile = importlib.util.cache_from_source(ok_py_path)
with open(cfile, 'rb') as f:
    f.read(16)
    decomp_code = marshal.load(f)

orig_map = _extract_code_objects(orig_code)
decomp_map = _extract_code_objects(decomp_code)

# Find _on_set_positions
for name in sorted(orig_map.keys()):
    if '_on_set_positions' in name:
        details = compare_bytecode(orig_map[name], decomp_map[name])
        if not details.get('match') and not details.get('jump_only'):
            true_diffs = details.get('true_diffs', [])
            print(f"\n{name}: {len(true_diffs)} true_diffs")
            if true_diffs:
                td = true_diffs[0]
                idx = td['index']
                orig_filtered = _filter_noise_instrs(list(dis.get_instructions(orig_map[name])))
                decomp_filtered = _filter_noise_instrs(list(dis.get_instructions(decomp_map[name])))
                print(f"  First diff at idx {idx}: orig={td.get('orig_op')} decomp={td.get('decomp_op')}")
                print(f"  Orig context: {[(i.opname, getattr(i,'argval',None)) for i in orig_filtered[max(0,idx-3):idx+5]]}")
                print(f"  Decomp context: {[(i.opname, getattr(i,'argval',None)) for i in decomp_filtered[max(0,idx-3):idx+5]]}")
