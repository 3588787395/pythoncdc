import sys
sys.path.insert(0, '.')
from testqouter.round1.base import compare_bytecode, _filter_noise_instrs, get_bytecode_instructions
import marshal, types

def load_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def extract_func(code, name):
    if code.co_name == name:
        return code
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            r = extract_func(c, name)
            if r: return r
    return None

orig_code = load_code('site-packages/fly/common/tradingday_calendar.pyc')
orig_func = extract_func(orig_code, 'get_start_day')

instrs = list(_filter_noise_instrs(get_bytecode_instructions(orig_func)))
print(f"orig: {len(instrs)} instructions")
for i, instr in enumerate(instrs):
    print(f"  {i:3d} {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
