"""Analyze common defect patterns across partial pyc files."""
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
partials = [e for e in entries if e.get('decompile_status') == 'partial']
partials.sort(key=lambda e: e.get('bytecode_match_rate', 0))

# Analyze first 20 partial files
from collections import Counter
pattern_counter = Counter()
detail_list = []

for entry in partials[:20]:
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
        continue
    
    try:
        cfile = py_compile.compile(ok_py_path, doraise=True, quiet=2)
        with open(cfile, 'rb') as f:
            f.read(16)
            decomp_code = marshal.load(f)
    except Exception as e:
        print(f"  COMPILE FAIL: {pyc_path}: {e}")
        continue
    
    decomp_map = extract_code_objects(decomp_code)
    common = set(orig_map.keys()) & set(decomp_map.keys())
    
    for name in sorted(common):
        cmp = compare_bytecode(orig_map[name], decomp_map[name])
        if cmp.get('match') or cmp.get('jump_only'):
            continue
        true_diffs = cmp.get('true_diffs', [])
        for td in true_diffs[:3]:  # first 3 diffs per function
            orig_op = td.get('orig_op', '?')
            decomp_op = td.get('decomp_op', '?')
            orig_arg = td.get('orig_arg', '?')
            decomp_arg = td.get('decomp_arg', '?')
            
            # Classify pattern
            if orig_op == 'LOAD_DEREF' and decomp_op == 'LOAD_GLOBAL':
                pattern = 'LOAD_DEREF->LOAD_GLOBAL (closure var as global)'
            elif orig_op == 'LOAD_GLOBAL' and decomp_op == 'LOAD_CLOSURE':
                pattern = 'LOAD_GLOBAL->LOAD_CLOSURE (global as closure)'
            elif orig_op == 'LOAD_FAST' and decomp_op == 'POP_TOP':
                pattern = 'LOAD_FAST->POP_TOP (expression dropped)'
            elif orig_op != decomp_op:
                pattern = f'{orig_op}->{decomp_op} (op mismatch)'
            elif orig_arg != decomp_arg:
                pattern = f'{orig_op} arg mismatch: {orig_arg}->{decomp_arg}'
            else:
                pattern = 'other'
            
            pattern_counter[pattern] += 1
            detail_list.append({
                'pyc': os.path.basename(pyc_path),
                'func': name,
                'pattern': pattern,
                'orig': f'{orig_op}({orig_arg})',
                'decomp': f'{decomp_op}({decomp_arg})',
            })

print("=== Common defect patterns (first 20 partial files) ===")
for pattern, count in pattern_counter.most_common(30):
    print(f"  {count:4d}  {pattern}")

print("\n=== Sample details ===")
for d in detail_list[:30]:
    print(f"  {d['pyc']:30s}  {d['func']:30s}  {d['orig']:30s} -> {d['decomp']:30s}  [{d['pattern']}]")
