import sys, json, marshal, types, py_compile
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

for entry in json.load(open('pyc_index.json', 'r', encoding='utf-8')):
    if entry.get('decompile_status') != 'partial':
        continue
    pyc_path = entry['path']
    ok_py_path = pyc_path[:-4] + 'OK.py'
    import os
    if not os.path.exists(ok_py_path):
        continue
    try:
        orig_code = _load_pyc_code(pyc_path)
        cfile = py_compile.compile(ok_py_path, doraise=True, quiet=2)
        with open(cfile, 'rb') as f:
            f.read(16)
            decomp_code = marshal.load(f)
    except:
        continue
    orig_map = _extract_code_objects(orig_code)
    decomp_map = _extract_code_objects(decomp_code)
    for name in sorted(set(orig_map.keys()) & set(decomp_map.keys())):
        details = compare_bytecode(orig_map[name], decomp_map[name])
        if details.get('match'):
            continue
        td = details.get('true_diffs', [])
        for t in td:
            if t.get('orig_op','') == 'LOAD_DEREF' and t.get('decomp_op','') == 'LOAD_GLOBAL':
                ocode = orig_map[name]
                varname = t.get('orig_arg', '')
                print('%s: var=%s in_freevars=%s in_cellvars=%s' % (
                    name.split('.')[-1], varname,
                    varname in ocode.co_freevars,
                    varname in ocode.co_cellvars))
                break
