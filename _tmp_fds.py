import marshal, types, dis, sys
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from pycdc import decompile_pyc

pyc_path = r'F:\Downloads\pythoncdc-main\site-packages\IQData\plugins\plugin_system_local_finance\finance_data_source.pyc'
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

func = find_func(code, 'growth_factors_sql_get')
print("Original co_varnames:", func.co_varnames)
print("Original co_names:", func.co_names)

# Now decompile and check
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

decomp_func = find_func(decomp_code, 'growth_factors_sql_get')
print("\nDecompiled co_varnames:", decomp_func.co_varnames)
print("Decompiled co_names:", decomp_func.co_names)

# Compare
print("\nvarnames diff:")
for i, (o, d) in enumerate(zip(func.co_varnames, decomp_func.co_varnames)):
    if o != d:
        print(f"  [{i}] orig={o!r} decomp={d!r}")
