#!/usr/bin/env python3
"""R100: Analyze top diff functions in remaining partial pyc files"""
import sys, types, marshal, dis, json, os
from collections import Counter
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import compare_bytecode, get_bytecode_instructions, _filter_noise_instrs

with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    pyc_index = json.load(f)

# Collect all diff functions
diff_functions = []
for entry in pyc_index:
    if entry.get('decompile_status') != 'partial':
        continue
    pyc_path = entry['path']
    ok_path = pyc_path.replace('.pyc', 'OK.py')
    if not os.path.exists(pyc_path) or not os.path.exists(ok_path):
        continue
    try:
        with open(pyc_path, 'rb') as f:
            f.read(16)
            orig_code = marshal.load(f)
        with open(ok_path, 'r', encoding='utf-8') as f:
            source = f.read()
        decomp_code = compile(source, ok_path, 'exec')
    except:
        continue
    
    def extract(co):
        r = {co.co_name: co}
        for c in co.co_consts:
            if isinstance(c, types.CodeType):
                r.update(extract(c))
        return r
    
    om = extract(orig_code)
    dm = extract(decomp_code)
    
    for name in om:
        if name not in dm or name.startswith('<'):
            continue
        oi = _filter_noise_instrs(get_bytecode_instructions(om[name]))
        di = _filter_noise_instrs(get_bytecode_instructions(dm[name]))
        result = compare_bytecode(om[name], dm[name])
        diffs = len(result['true_diffs'])
        if diffs > 0:
            len_diff = len(oi) - len(di)
            diff_functions.append((os.path.basename(pyc_path), name, len(oi), len(di), len_diff, diffs))

# Sort by len_diff (lost instructions)
print("Top 25 functions by lost instructions (orig - decomp):")
for pyc, func, oi, di, ld, diffs in sorted(diff_functions, key=lambda x: -x[4])[:25]:
    print(f"  {pyc}::{func}: orig={oi}, decomp={di}, lost={ld}, diffs={diffs}")

# Also sort by diff count
print(f"\nTop 25 by diff count:")
for pyc, func, oi, di, ld, diffs in sorted(diff_functions, key=lambda x: -x[5])[:25]:
    print(f"  {pyc}::{func}: orig={oi}, decomp={di}, lost={ld}, diffs={diffs}")

# Categorize by len_diff pattern
small_diff = sum(1 for _, _, _, _, ld, d in diff_functions if abs(ld) <= 5 and d <= 10)
medium_diff = sum(1 for _, _, _, _, ld, d in diff_functions if abs(ld) > 5 and ld < 50)
large_diff = sum(1 for _, _, _, _, ld, d in diff_functions if ld >= 50)
print(f"\nCategories:")
print(f"  Small diff (|len_diff|<=5, diffs<=10): {small_diff}")
print(f"  Medium diff (5<lost<50): {medium_diff}")
print(f"  Large diff (lost>=50): {large_diff}")
