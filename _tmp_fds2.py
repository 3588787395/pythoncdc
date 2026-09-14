import marshal, types, dis, sys
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from pycdc import decompile_pyc

pyc_path = r'F:\Downloads\pythoncdc-main\site-packages\IQData\plugins\plugin_system_local_finance\finance_data_source.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_all_funcs(code_obj, prefix=''):
    result = {}
    name = code_obj.co_name
    full = f"{prefix}{name}"
    result[full] = code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            result.update(find_all_funcs(const, f"{full}."))
    return result

orig_funcs = find_all_funcs(code)

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

decomp_funcs = find_all_funcs(decomp_code)

# Compare all
for name in orig_funcs:
    if name in decomp_funcs:
        o = orig_funcs[name]
        d = decomp_funcs[name]
        if o.co_varnames != d.co_varnames:
            print(f"\n{name} co_varnames DIFF:")
            print(f"  orig:  {o.co_varnames}")
            print(f"  decomp: {d.co_varnames}")
        if o.co_names != d.co_names:
            print(f"\n{name} co_names DIFF:")
            print(f"  orig:  {o.co_names}")
            print(f"  decomp: {d.co_names}")
