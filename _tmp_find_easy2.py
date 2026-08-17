"""Find pyc files with the fewest true_diffs (easiest to fix)."""
import json
import os
import sys
import dis
import marshal
import types
import py_compile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load pyc index
data = json.load(open('pyc_index.json', 'r', encoding='utf-8'))
partials = [d for d in data if d.get('decompile_status') == 'partial']

# For each partial, decompile and check true_diffs
from testqouter.round1.base import compare_bytecode, decompile_pyc

results = []
for d in partials[:30]:  # Check first 30 partials
    pyc_path = d['path']
    try:
        # Load original
        with open(pyc_path, 'rb') as f:
            f.read(4); f.read(4); f.read(8)
            orig_code = marshal.load(f)
        
        # Decompile
        source = decompile_pyc(pyc_path)
        ok_path = pyc_path.replace('.pyc', 'OK.py')
        with open(ok_path, 'w', encoding='utf-8') as f:
            f.write(source)
        
        # Compile
        decomp_code = compile(source, ok_path, 'exec')
        
        # Compare all functions
        min_true_diffs = 999999
        min_func = None
        for const in orig_code.co_consts:
            if isinstance(const, types.CodeType):
                for inner in const.co_consts:
                    if isinstance(inner, types.CodeType):
                        try:
                            result = compare_bytecode(inner, _find_code(decomp_code, inner.co_name))
                            if not result['match'] and len(result['true_diffs']) < min_true_diffs:
                                min_true_diffs = len(result['true_diffs'])
                                min_func = inner.co_name
                        except:
                            pass
        
        if min_func:
            p = pyc_path.split('site-packages\\')[-1]
            results.append((min_true_diffs, min_func, p))
    except Exception as e:
        pass

results.sort()
print("Files with fewest true_diffs (easiest to fix):")
for td, func, path in results[:15]:
    print(f"  {td:4d} true_diffs - {func} - {path}")

def _find_code(code_obj, name):
    if code_obj.co_name == name:
        return code_obj
    for c in code_obj.co_consts:
        if isinstance(c, types.CodeType):
            r = _find_code(c, name)
            if r:
                return r
    return None
