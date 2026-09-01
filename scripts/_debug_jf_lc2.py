import sys, marshal, types, dis, os, py_compile, importlib.util
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

pyc_path = 'site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc'
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

for name in sorted(orig_map.keys()):
    if 'option_covered_trans' in name:
        orig_instrs = _filter_noise_instrs(get_bytecode_instructions(orig_map[name]))
        decomp_instrs = _filter_noise_instrs(get_bytecode_instructions(decomp_map[name]))
        print(f"orig last 5: {[(i.opname, getattr(i,'argval',None)) for i in orig_instrs[-5:]]}")
        print(f"decomp last 5: {[(i.opname, getattr(i,'argval',None)) for i in decomp_instrs[-5:]]}")
        print(f"orig len={len(orig_instrs)}, decomp len={len(decomp_instrs)}")
