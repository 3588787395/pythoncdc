"""Debug repro_21 try-except pattern."""
import dis, marshal, types, sys, py_compile
sys.path.insert(0, '.')

REPRO_DIR = ".trae/specs/region-comment-multi-pyc-iteration/rounds/round_46/test_engineer/minimal_repros"

# Original
with open(f'{REPRO_DIR}/repro_21_try_except_format.pyc', 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

# Decompiled
cfile = py_compile.compile(f'{REPRO_DIR}/repro_21_try_except_formatOK.py', doraise=True, quiet=2)
with open(cfile, 'rb') as f:
    f.read(16)
    decomp_code = marshal.load(f)

def find_func(code, name):
    for const in code.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == name:
            return const
    return None

orig_func = find_func(orig_code, 'func')
decomp_func = find_func(decomp_code, 'func')

print("=== ORIGINAL func ===")
dis.dis(orig_func)

print("\n=== DECOMPILED func ===")
dis.dis(decomp_func)
