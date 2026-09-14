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

orig_func = find_func(code, 'post')
orig_instrs = list(dis.get_instructions(orig_func))

source = decompile_pyc(pyc_path)
ok_path = pyc_path.replace('.pyc', 'OK.py')
with open(ok_path, 'w', encoding='utf-8') as f:
    f.write(source)

py_compile.compile(ok_path, doraise=True, quiet=2)
cfile = importlib.util.cache_from_source(ok_path)
with open(cfile, 'rb') as f:
    f.read(16)
    decomp_code = marshal.load(f)

decomp_func = find_func(decomp_code, 'post')
decomp_instrs = list(dis.get_instructions(decomp_func))

# Side by side comparison, first 100
max_len = max(len(orig_instrs), len(decomp_instrs))
for i in range(min(max_len, 100)):
    o = orig_instrs[i] if i < len(orig_instrs) else None
    d = decomp_instrs[i] if i < len(decomp_instrs) else None
    o_str = f"{o.offset:4d} {o.opname:30s} {o.argrepr}" if o else ""
    d_str = f"{d.offset:4d} {d.opname:30s} {d.argrepr}" if d else ""
    marker = " <<<" if (o and d and (o.opname != d.opname or o.offset != d.offset)) else ""
    print(f"  {i:3d} ORIG: {o_str:60s} DEC: {d_str}{marker}")
