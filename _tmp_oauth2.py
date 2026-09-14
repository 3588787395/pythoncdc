import marshal, types, dis, sys, os
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from pycdc import decompile_pyc
import py_compile, importlib.util

pyc_path = r'F:\Downloads\pythoncdc-main\site-packages\fly\oauthenticator\oauth2.pyc'

with open(pyc_path, 'rb') as f:
    magic = f.read(4)
    flags = int.from_bytes(f.read(4), 'little')
    f.read(8)
    code = marshal.load(f)

def find_func(code_obj, name):
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            r = find_func(const, name)
            if r: return r
    return None

func = find_func(code, 'post')
print("=== ORIGINAL post() ===")
for i, instr in enumerate(dis.get_instructions(func)):
    print(f"  {i:3d}: {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
