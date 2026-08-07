import sys, types, marshal, os
sys.path.insert(0, '.')
from pycdc import decompile_pyc

pyc_path = 'site-packages/IQData/plugins/plugin_system_db/iqdata_db_base.pyc'

with open(pyc_path, 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

source = decompile_pyc(pyc_path)
decomp_code = compile(source, '<decompiled>', 'exec')

def find_code_objects(code, prefix=''):
    result = {prefix or code.co_name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            child_name = f"{prefix}.{const.co_name}" if prefix else const.co_name
            result.update(find_code_objects(const, child_name))
    return result

orig_map = find_code_objects(orig_code)
decomp_map = find_code_objects(decomp_code)

# Compare co_name for all code objects
print("=== Code object name comparison ===")
for name in sorted(orig_map.keys()):
    orig_co_name = orig_map[name].co_name
    if name in decomp_map:
        decomp_co_name = decomp_map[name].co_name
        if orig_co_name != decomp_co_name:
            print(f"  MISMATCH: {name}")
            print(f"    orig co_name: {orig_co_name}")
            print(f"    decomp co_name: {decomp_co_name}")
    else:
        print(f"  MISSING in decomp: {name} (co_name={orig_co_name})")

# Also check if there are extra code objects in decomp
for name in sorted(decomp_map.keys()):
    if name not in orig_map:
        print(f"  EXTRA in decomp: {name} (co_name={decomp_map[name].co_name})")

print("\n=== All code objects with __ in co_name ===")
for name, code in sorted(orig_map.items()):
    if '__' in code.co_name and not code.co_name.startswith('__'):
        print(f"  orig: {name} -> co_name={code.co_name}")
for name, code in sorted(decomp_map.items()):
    if '__' in code.co_name and not code.co_name.startswith('__'):
        print(f"  decomp: {name} -> co_name={code.co_name}")
