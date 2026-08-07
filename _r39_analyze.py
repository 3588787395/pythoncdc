import sys, os, types, marshal, dis
sys.path.insert(0, '.')
from pycdc import decompile_pyc as _decompile
from testqouter.round1.base import compare_bytecode, get_bytecode_instructions, decompile_pyc as base_decompile

files = [
    'site-packages/IQEngine/core/engine/engine.pyc',
    'site-packages/IQEngine/plugins/plugin_system_accounts/position_model/live_future_position.pyc',
]

def collect_all_code_objects(code, prefix=''):
    """Recursively collect all code objects including nested."""
    result = {}
    if prefix:
        result[prefix] = code
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            name = c.co_name if not prefix else f"{prefix}.{c.co_name}"
            result[name] = c
            # Also collect nested code objects
            for nc in c.co_consts:
                if isinstance(nc, types.CodeType):
                    result[f"{name}.{nc.co_name}"] = nc
                    for nnc in nc.co_consts:
                        if isinstance(nnc, types.CodeType):
                            result[f"{name}.{nc.co_name}.{nnc.co_name}"] = nnc
    return result

for pyc_path in files:
    print(f"\n{'='*60}")
    print(f"File: {pyc_path}")
    
    with open(pyc_path, 'rb') as f:
        f.read(16)
        orig_code = marshal.load(f)
    
    source = base_decompile(pyc_path)
    
    try:
        decomp_code = compile(source, '<decompiled>', 'exec')
    except SyntaxError as e:
        print(f"  SyntaxError: {e}")
        continue
    
    orig_all = collect_all_code_objects(orig_code)
    decomp_all = collect_all_code_objects(decomp_code)
    
    total = 0
    matched = 0
    for name, orig_func in orig_all.items():
        total += 1
        if name in decomp_all:
            result = compare_bytecode(orig_func, decomp_all[name])
            if result['match']:
                matched += 1
            else:
                print(f"\n  MISMATCH: {name}")
                # Show first difference
                oo = result['orig_ops']
                do = result['decomp_ops']
                for i in range(min(len(oo), len(do))):
                    if oo[i] != do[i]:
                        start = max(0, i-3)
                        print(f"  First diff at index {i}:")
                        print(f"    Orig:  {oo[start:i+5]}")
                        print(f"    Decomp: {do[start:i+5]}")
                        break
                else:
                    print(f"  Length diff: orig={len(oo)} decomp={len(do)}")
                    if len(oo) > len(do):
                        print(f"  Extra in orig: {oo[len(do):]}")
                    else:
                        print(f"  Extra in decomp: {do[len(oo):]}")
        else:
            print(f"\n  MISSING: {name}")
    
    print(f"\n  Total: {total}, Matched: {matched}, Rate: {matched/total*100:.2f}%")
