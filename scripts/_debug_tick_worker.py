import sys
sys.path.insert(0, '.')
from testqouter.round1.base import get_bytecode_instructions
import marshal, types, dis

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

code = load_code('site-packages/IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc')
func = extract_func(code, 'tick_worker_thread')
if func:
    instrs = list(get_bytecode_instructions(func))
    print(f'tick_worker_thread: {len(instrs)} instructions')
    for i, instr in enumerate(instrs):
        print(f'  {i:3d} {instr.offset:4d} {instr.opname:30s} {instr.argrepr}')
else:
    print('Function not found')
