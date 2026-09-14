import marshal, types, dis, sys, os
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from pycdc import decompile_pyc
import py_compile, importlib.util

pyc_path = r'F:\Downloads\pythoncdc-main\site-packages\fly\oauthenticator\oauth2.pyc'

source = decompile_pyc(pyc_path)
ok_path = pyc_path.replace('.pyc', 'OK.py')
with open(ok_path, 'w', encoding='utf-8') as f:
    f.write(source)

py_compile.compile(ok_path, doraise=True, quiet=2)
cfile = importlib.util.cache_from_source(ok_path)
with open(cfile, 'rb') as f:
    f.read(16)
    decomp_code = marshal.load(f)

def find_func(code_obj, name):
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            r = find_func(const, name)
            if r: return r
    return None

func = find_func(decomp_code, 'post')
print("=== DECOMPILED post() ===")
for i, instr in enumerate(dis.get_instructions(func)):
    print(f"  {i:3d}: {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
