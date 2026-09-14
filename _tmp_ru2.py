import sys, os, marshal, types
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode, get_bytecode_instructions
import dis

pyc_path = r'F:\Downloads\pythoncdc-main\site-packages\IQCommon\util\replace_utils.pyc'

# Load original
with open(pyc_path, 'rb') as f:
    magic = f.read(4)
    flags = int.from_bytes(f.read(4), 'little')
    if flags & 0x1:
        f.read(8)
    else:
        f.read(8)
    code = marshal.load(f)

def get_func_map(code_obj):
    result = {}
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            result[const.co_name] = const
            result.update(get_func_map(const))
    return result

orig_funcs = get_func_map(code)

# Decompile and compile
source = decompile_pyc(pyc_path)
ok_path = pyc_path.replace('.pyc', 'OK.py')
with open(ok_path, 'w', encoding='utf-8') as f:
    f.write(source)

import py_compile, importlib.util
py_compile.compile(ok_path, doraise=True, quiet=2)
cfile = importlib.util.cache_from_source(ok_path)
with open(cfile, 'rb') as f:
    f.read(16)
    decomp_code = marshal.load(f)

decomp_funcs = get_func_map(decomp_code)

fname = 'decrypt_database_url'
if fname in orig_funcs and fname in decomp_funcs:
    print("=== ORIGINAL ===")
    for i, instr in enumerate(dis.get_instructions(orig_funcs[fname])):
        print(f"  {i:3d}: {instr.offset:4d} {instr.opname} {instr.argrepr}")
    print()
    print("=== DECOMPILED ===")
    for i, instr in enumerate(dis.get_instructions(decomp_funcs[fname])):
        print(f"  {i:3d}: {instr.offset:4d} {instr.opname} {instr.argrepr}")
else:
    print(f"Function {fname} not found. orig={fname in orig_funcs}, decomp={fname in decomp_funcs}")
