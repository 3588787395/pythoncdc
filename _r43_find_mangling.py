import sys, types, marshal, dis, os
sys.path.insert(0, '.')
from pycdc import decompile_pyc

# Find the actual file with __load_table_names
# Check multiple possible paths
paths = [
    'site-packages/IQData/plugins/plugin_system_db/iqdata_db_base.pyc',
    'site-packages/IQData/plugins/plugin_system_db_tools/iqdata_db_base.pyc',
    'site-packages/IQData/plugins/plugin_system_db/db_base.pyc',
]

# Search for the file
import json
with open('pyc_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for entry in data:
    path = entry.get('path', '')
    basename = os.path.basename(path)
    if 'iqdata_db_base' in basename or 'db_base' in basename:
        print(f"Found: {path}")
        
        with open(path, 'rb') as f:
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
        
        print("  Code objects with __ in name:")
        for name, code in sorted(code_map.items()):
            if '__' in code.co_name and not code.co_name.startswith('__'):
                print(f"    {name} -> co_name={code.co_name}")
        
        # Also check decompiled
        source = decompile_pyc(path)
        decomp_code = compile(source, '<decompiled>', 'exec')
        decomp_map = find_code_objects(decomp_code)
        
        print("  Decompiled code objects with __ in name:")
        for name, code in sorted(decomp_map.items()):
            if '__' in code.co_name and not code.co_name.startswith('__'):
                print(f"    {name} -> co_name={code.co_name}")
        
        # Compare
        print("\n  Name mismatches:")
        orig_names = set(code_map.keys())
        decomp_names = set(decomp_map.keys())
        for name in sorted(orig_names & decomp_names):
            if code_map[name].co_name != decomp_map[name].co_name:
                print(f"    {name}: orig={code_map[name].co_name} vs decomp={decomp_map[name].co_name}")
        break
