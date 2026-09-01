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

# Find clock_worker
for entry in json.load(open('pyc_index.json', 'r', encoding='utf-8')):
    if 'scheduler' not in entry.get('path', '') and 'IQEngine' not in entry.get('path', ''):
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
        if 'clock_worker' not in name:
            continue
        ocode = orig_map[name]
        dcode = decomp_map[name]
        
        closure_vars = set(ocode.co_freevars) | set(ocode.co_cellvars)
        print('name:', name)
        print('freevars:', ocode.co_freevars)
        print('cellvars:', ocode.co_cellvars)
        print('closure_vars:', closure_vars)
        
        # Check decomp instructions for LOAD_GLOBAL
        decomp_instrs = list(_filter_noise_instrs(get_bytecode_instructions(dcode)))
        orig_instrs = list(_filter_noise_instrs(get_bytecode_instructions(ocode)))
        
        for i, instr in enumerate(decomp_instrs):
            if instr.opname == 'LOAD_GLOBAL' and instr.argval in closure_vars:
                print('FOUND: decomp[%d] = LOAD_GLOBAL(%s) should be LOAD_DEREF' % (i, instr.argval))
        for i, instr in enumerate(orig_instrs):
            if instr.opname == 'LOAD_DEREF' and instr.argval in closure_vars:
                print('ORIG: orig[%d] = LOAD_DEREF(%s)' % (i, instr.argval))
        
        # Also check: is self in decomp's LOAD_GLOBAL with NULL prefix?
        for i, instr in enumerate(decomp_instrs):
            if instr.opname == 'LOAD_GLOBAL' and 'self' in str(instr.argval):
                print('decomp[%d] = LOAD_GLOBAL(%s, arg=%s)' % (i, instr.argval, instr.arg))
        
        break
