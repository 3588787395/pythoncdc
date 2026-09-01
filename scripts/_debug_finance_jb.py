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

# Check func_get_fundamentals_daily_data which has 12 diffs
for entry in index:
    if 'finance' not in entry.get('path', '') or 'IQCommon' not in entry.get('path', ''):
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
        if 'func_get_fundamentals_daily_data' not in name:
            continue
        details = compare_bytecode(orig_map[name], decomp_map[name])
        if details.get('match') or details.get('jump_only'):
            continue
        true_diffs = details.get('true_diffs', [])
        
        # Find the JUMP_BACKWARD -> JUMP_FORWARD diff
        for td in true_diffs:
            if 'JUMP_BACKWARD' in td.get('orig_op', '') and 'JUMP_FORWARD' in td.get('decomp_op', ''):
                idx = td['index']
                orig_instrs = list(_filter_noise_instrs(get_bytecode_instructions(orig_map[name])))
                decomp_instrs = list(_filter_noise_instrs(get_bytecode_instructions(decomp_map[name])))
                print(f"JB->JF at idx={idx}")
                print("  orig context:")
                for i in range(max(0,idx-4), min(len(orig_instrs), idx+3)):
                    print(f"    {i:3d} {orig_instrs[i].opname:30s} {orig_instrs[i].argrepr}")
                print("  decomp context:")
                for i in range(max(0,idx-4), min(len(decomp_instrs), idx+3)):
                    print(f"    {i:3d} {decomp_instrs[i].opname:30s} {decomp_instrs[i].argrepr}")
                break
    break
