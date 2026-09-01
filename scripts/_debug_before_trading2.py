import sys, marshal, types, py_compile
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

orig_code = _load_pyc_code('site-packages/IQEngine/utils/scheduler.pyc')
cfile = py_compile.compile('site-packages/IQEngine/utils/schedulerOK.py', doraise=True, quiet=2)
with open(cfile, 'rb') as f:
    f.read(16)
    decomp_code = marshal.load(f)

orig_map = _extract_code_objects(orig_code)
decomp_map = _extract_code_objects(decomp_code)

name = '<module>.Scheduler.on_before_trading'
details = compare_bytecode(orig_map[name], decomp_map[name])
print(f'match={details.get("match")}, jump_only={details.get("jump_only")}')
print(f'true_diffs={len(details.get("true_diffs", []))}')
for td in details.get('true_diffs', []):
    print(f'  idx={td["index"]}: orig={td["orig_op"]}({td.get("orig_arg","")}) decomp={td["decomp_op"]}({td.get("decomp_arg","")})')
