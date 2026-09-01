import sys, json, marshal, types, py_compile, os
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

# ptrade_broker.pyc create_portfolio
for entry in json.load(open('pyc_index.json', 'r', encoding='utf-8')):
    if 'ptrade_broker.pyc' not in entry.get('path', ''):
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
        if 'create_portfolio' not in name:
            continue
        details = compare_bytecode(orig_map[name], decomp_map[name])
        if details.get('match') or details.get('jump_only'):
            continue
        true_diffs = details.get('true_diffs', [])
        print("Function: %s, %d true_diffs" % (name, len(true_diffs)))
        for td in true_diffs[:8]:
            print("  idx=%d: orig=%s(%s) decomp=%s(%s)" % (
                td['index'], td.get('orig_op',''), td.get('orig_arg',''),
                td.get('decomp_op',''), td.get('decomp_arg','')))
        
        # Show full context around the JB/JF
        orig_instrs = list(_filter_noise_instrs(get_bytecode_instructions(orig_map[name])))
        decomp_instrs = list(_filter_noise_instrs(get_bytecode_instructions(decomp_map[name])))
        for td in true_diffs:
            if 'JUMP_BACKWARD' in td.get('orig_op', ''):
                idx = td['index']
                print("\nOrig around idx=%d:" % idx)
                for i in range(max(0,idx-3), min(len(orig_instrs), idx+4)):
                    print("  %3d %s %s" % (i, orig_instrs[i].opname, orig_instrs[i].argrepr if hasattr(orig_instrs[i], 'argrepr') else orig_instrs[i].argval))
                print("Decomp around idx=%d:" % idx)
                for i in range(max(0,idx-3), min(len(decomp_instrs), idx+4)):
                    print("  %3d %s %s" % (i, decomp_instrs[i].opname, decomp_instrs[i].argrepr if hasattr(decomp_instrs[i], 'argrepr') else decomp_instrs[i].argval))
                break
    break
