import marshal, types, dis, sys
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from pycdc import decompile_pyc
import py_compile, importlib.util

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

orig_func = find_func(code, 'growth_factors_sql_get')

source = decompile_pyc(pyc_path)
ok_path = pyc_path.replace('.pyc', 'OK.py')
with open(ok_path, 'w', encoding='utf-8') as f:
    f.write(source)

py_compile.compile(ok_path, doraise=True, quiet=2)
cfile = importlib.util.cache_from_source(ok_path)
with open(cfile, 'rb') as f:
    f.read(16)
    decomp_code = marshal.load(f)

decomp_func = find_func(decomp_code, 'growth_factors_sql_get')

orig_instrs = list(dis.get_instructions(orig_func))
decomp_instrs = list(dis.get_instructions(decomp_func))

# Find first diff
for i in range(min(len(orig_instrs), len(decomp_instrs))):
    o = orig_instrs[i]
    d = decomp_instrs[i]
    if o.opname != d.opname or o.arg != d.arg or o.argrepr != d.argrepr:
        start = max(0, i-3)
        for j in range(start, min(i+8, max(len(orig_instrs), len(decomp_instrs)))):
            o2 = orig_instrs[j] if j < len(orig_instrs) else None
            d2 = decomp_instrs[j] if j < len(decomp_instrs) else None
            o_str = f"{o2.offset:4d} {o2.opname:25s} {o2.argrepr}" if o2 else "N/A"
            d_str = f"{d2.offset:4d} {d2.opname:25s} {d2.argrepr}" if d2 else "N/A"
            marker = " <<<" if (o2 and d2 and o2.opname != d2.opname) else ""
            print(f"  {j:4d} ORIG: {o_str:50s} DEC: {d_str}{marker}")
        break

print(f"\norig total: {len(orig_instrs)}, decomp total: {len(decomp_instrs)}")
