import sys, types, marshal, dis
sys.path.insert(0, '.')

pyc_path = 'site-packages/IQData/plugins/plugin_system_db_tools/db_base.pyc'

with open(pyc_path, 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

def find_code_objects(code, prefix=''):
    result = {prefix or code.co_name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            child_name = f"{prefix}.{const.co_name}" if prefix else const.co_name
            result.update(find_code_objects(const, child_name))
    return result

code_map = find_code_objects(orig_code)

print("=== Code objects with __ in name ===")
for name, code in sorted(code_map.items()):
    if '__' in name and not name.startswith('<'):
        print(f"  {name} (co_name={code.co_name})")

# Find the specific class that contains __load_table_names
print("\n=== Looking for class with __load_table_names ===")
for name, code in sorted(code_map.items()):
    if 'load_table' in name:
        print(f"  Found: {name}")
        print(f"    co_name: {code.co_name}")
        print(f"    co_varnames: {code.co_varnames}")
