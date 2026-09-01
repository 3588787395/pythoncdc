import sys, marshal, types, dis
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
orig_map = _extract_code_objects(orig_code)

# Find on_before_trading
for name, code in sorted(orig_map.items()):
    if 'on_before_trading' in name and '<dictcomp>' not in name and '<listcomp>' not in name:
        print(f"\n=== {name} ===")
        instrs = list(get_bytecode_instructions(code))
        for i, instr in enumerate(instrs):
            print(f"  {i:3d} {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
