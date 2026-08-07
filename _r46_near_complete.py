"""Find pyc files close to 100% match rate and analyze their remaining defects."""
import json, sys, marshal, types, py_compile, os
sys.path.insert(0, '.')
from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode

def load_pyc_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def extract_code_objects(code_obj):
    result = {}
    name = code_obj.co_name or '<module>'
    result[name] = code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const))
    return result

entries = json.load(open('pyc_index.json', 'r', encoding='utf-8'))
# Find partials with high match rates (close to 100%)
near_complete = [e for e in entries if e.get('decompile_status') == 'partial' and e.get('bytecode_match_rate', 0) >= 0.80]
near_complete.sort(key=lambda e: e.get('bytecode_match_rate', 0), reverse=True)

print(f"=== Partial files with >=80% match rate ({len(near_complete)} files) ===")
for e in near_complete[:30]:
    rate = e.get('bytecode_match_rate', 0)
    fc = e.get('function_count', 0)
    path = e.get('path', '')
    # Count mismatched functions
    mismatched = fc - int(round(fc * rate))
    print(f"  {rate:.2%}  {fc:3d} funcs  {mismatched:2d} bad  {os.path.basename(path)}")

# Analyze defects for top 10 near-complete files
print("\n=== Defect details for near-complete files ===")
from collections import Counter
pattern_counter = Counter()

for entry in near_complete[:15]:
    pyc_path = entry['path']
    if not os.path.exists(pyc_path):
        continue
    try:
        orig_code = load_pyc_code(pyc_path)
    except:
        continue
    orig_map = extract_code_objects(orig_code)
    
    ok_py_path = pyc_path.replace('.pyc', 'OK.py')
    if not os.path.exists(ok_py_path):
        # Re-decompile
        try:
            src = decompile_pyc(pyc_path)
            if src:
                with open(ok_py_path, 'w', encoding='utf-8') as f:
                    f.write(src)
        except:
            continue
    
    try:
        cfile = py_compile.compile(ok_py_path, doraise=True, quiet=2)
        with open(cfile, 'rb') as f:
            f.read(16)
            decomp_code = marshal.load(f)
    except Exception as e:
        continue
    
    decomp_map = extract_code_objects(decomp_code)
    common = set(orig_map.keys()) & set(decomp_map.keys())
    
    for name in sorted(common):
        cmp = compare_bytecode(orig_map[name], decomp_map[name])
        if cmp.get('match') or cmp.get('jump_only'):
            continue
        true_diffs = cmp.get('true_diffs', [])
        if not true_diffs:
            continue
        
        td = true_diffs[0]
        orig_op = td.get('orig_op', '?')
        decomp_op = td.get('decomp_op', '?')
        orig_arg = td.get('orig_arg', '?')
        decomp_arg = td.get('decomp_arg', '?')
        
        if orig_op == decomp_op and orig_arg != decomp_arg:
            pattern = f'{orig_op} arg: {orig_arg}->{decomp_arg}'
        elif orig_op != decomp_op:
            pattern = f'{orig_op}->{decomp_op}'
        else:
            pattern = 'other'
        
        pattern_counter[pattern] += 1
        print(f"  {os.path.basename(pyc_path):35s}  {name:30s}  {orig_op}({orig_arg}) -> {decomp_op}({decomp_arg})")

print("\n=== Pattern summary ===")
for pattern, count in pattern_counter.most_common(20):
    print(f"  {count:4d}  {pattern}")
