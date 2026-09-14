import marshal, types, dis, sys
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from pycdc import decompile_pyc
import py_compile, importlib.util

pyc_path = r'F:\Downloads\pythoncdc-main\site-packages\IQEngine\plugins\plugin_system_event_source\realtime_event_source.pyc'

with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_func(code_obj, name):
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            r = find_func(const, name)
            if r: return r
    return None

orig_func = find_func(code, 'clock_worker')
orig_instrs = list(dis.get_instructions(orig_func))

# Find first_diff area around index 666
for i in range(660, min(680, len(orig_instrs))):
    instr = orig_instrs[i]
    print(f"  {i:3d}: {instr.offset:4d} {instr.opname:30s} arg={instr.arg} {instr.argrepr}")
