import sys, types, marshal, dis
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

pyc_path = 'F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_risk_calculation/function.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

ok_path = pyc_path.replace('.pyc', 'OK.py')
import py_compile
cfile = py_compile.compile(ok_path, doraise=True, quiet=2)
with open(cfile, 'rb') as f:
    f.read(16)
    decomp_code = marshal.load(f)

from testqouter.round1.base import compare_bytecode

def extract_code_objects(code_obj):
    result = {}
    name = code_obj.co_name or '<module>'
    result[name] = code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const))
    return result

orig_map = extract_code_objects(orig_code)
decomp_map = extract_code_objects(decomp_code)

name = 'backtest_info_writer'
cmp = compare_bytecode(orig_map[name], decomp_map[name])
print(f"MISMATCH: {name}")
print(f"  orig_count={cmp.get('orig_count')}, decomp_count={cmp.get('decomp_count')}")

true_diffs = cmp.get('true_diffs', [])
print(f"\ntrue_diffs ({len(true_diffs)} total):")
for td in true_diffs[:15]:
    print(f"  {td}")

# Show decompiled source
with open(ok_path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()
lines = content.split('\n')
in_func = False
func_lines = []
for line in lines:
    stripped = line.strip()
    if f'def {name}' in stripped:
        in_func = True
        func_lines.append(line)
        continue
    if in_func:
        current_indent = len(line) - len(line.lstrip()) if line.strip() else 999
        def_indent = len(func_lines[0]) - len(func_lines[0].lstrip()) if func_lines else 0
        if stripped and current_indent <= def_indent and func_lines:
            break
        func_lines.append(line)
print("\n--- Decompiled source ---")
for i, fl in enumerate(func_lines):
    print(f'{i+1:3d}: {fl}')
