import sys
sys.path.insert(0, '.')
from testqouter.round1.base import compare_bytecode, _filter_noise_instrs, get_bytecode_instructions
import marshal, types, py_compile

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

orig_code = load_code('site-packages/IQEngine/utils/__init__.pyc')
orig_func = extract_func(orig_code, 'wrapper')
if orig_func:
    print(f"wrapper co_freevars: {orig_func.co_freevars}")
    print(f"wrapper co_cellvars: {orig_func.co_cellvars}")
    print(f"wrapper co_names: {orig_func.co_names}")
    instrs = list(_filter_noise_instrs(get_bytecode_instructions(orig_func)))
    for i, instr in enumerate(instrs):
        print(f"  {i:3d} {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
else:
    print("wrapper not found in orig")

# Also check the decompiled version
cfile = py_compile.compile('site-packages/IQEngine/utils/__init__OK.py', doraise=True, quiet=2)
with open(cfile, 'rb') as f:
    f.read(16)
    decomp_code = marshal.load(f)
decomp_func = extract_func(decomp_code, 'wrapper')
if decomp_func:
    print(f"\nDecomp wrapper co_freevars: {decomp_func.co_freevars}")
    print(f"Decomp wrapper co_cellvars: {decomp_func.co_cellvars}")
    print(f"Decomp wrapper co_names: {decomp_func.co_names}")
    instrs = list(_filter_noise_instrs(get_bytecode_instructions(decomp_func)))
    for i, instr in enumerate(instrs):
        print(f"  {i:3d} {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
