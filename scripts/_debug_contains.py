import sys, marshal, types
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

orig_code = _load_pyc_code('site-packages/fly/data/quote.pyc')
orig_map = _extract_code_objects(orig_code)

import py_compile
cfile = py_compile.compile('site-packages/fly/data/quoteOK.py', doraise=True, quiet=2)
with open(cfile, 'rb') as f:
    f.read(16)
    decomp_code = marshal.load(f)
decomp_map = _extract_code_objects(decomp_code)

for name in sorted(set(orig_map.keys()) & set(decomp_map.keys())):
    if 'check_index_code' not in name:
        continue
    orig_instrs = list(_filter_noise_instrs(get_bytecode_instructions(orig_map[name])))
    decomp_instrs = list(_filter_noise_instrs(get_bytecode_instructions(decomp_map[name])))
    
    for i in range(min(len(orig_instrs), len(decomp_instrs))):
        o = orig_instrs[i]
        d = decomp_instrs[i]
        if o.opname == 'CONTAINS_OP':
            print('i=%d orig=%s(%s) decomp=%s(%s)' % (i, o.opname, o.argval, d.opname, d.argval))
            if i+1 < min(len(orig_instrs), len(decomp_instrs)):
                o_next = orig_instrs[i+1]
                d_next = decomp_instrs[i+1]
                print('  next orig=%s decomp=%s' % (o_next.opname, d_next.opname))
                o_is_true = o_next.opname.endswith('_TRUE')
                d_is_true = d_next.opname.endswith('_TRUE')
                print('  o_is_true=%s d_is_true=%s inverted=%s' % (o_is_true, d_is_true, o_is_true != d_is_true))
