#!/usr/bin/env python3
"""Analyze the most common failure patterns across all partial pyc files."""
import json
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))

from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode, get_bytecode_instructions
import marshal

def load_pyc_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def extract_code_objects(code_obj, prefix=""):
    result = {}
    name = prefix + code_obj.co_name if prefix else code_obj.co_name
    result[name] = code_obj
    for const in code_obj.co_consts:
        if hasattr(const, 'co_name'):
            child_prefix = prefix + code_obj.co_name + "." if prefix else code_obj.co_name + "."
            result.update(extract_code_objects(const, child_prefix))
    return result

idx = json.load(open('pyc_index.json', encoding='utf-8'))
partial = [e for e in idx if e['decompile_status'] == 'partial']
partial.sort(key=lambda e: e['function_count'] * (1 - e['bytecode_match_rate']), reverse=True)

# Analyze top 20 partial files
pattern_counter = Counter()
total_mismatch = 0

for entry in partial[:20]:
    pyc_path = entry['path']
    try:
        source = decompile_pyc(pyc_path)
        if source is None:
            continue
        # Generate OK.py
        ok_path = pyc_path.replace('.pyc', 'OK.py')
        with open(ok_path, 'w', encoding='utf-8') as f:
            f.write(source)

        # Compare bytecode
        orig_code = load_pyc_code(pyc_path)
        result = compare_bytecode(orig_code, ok_path)

        if isinstance(result, dict):
            for func_name, diffs in result.items():
                if diffs:
                    total_mismatch += 1
                    for diff in diffs[:3]:  # First 3 diffs per function
                        if isinstance(diff, tuple) and len(diff) >= 2:
                            orig_instr = diff[0]
                            decomp_instr = diff[1]
                            if orig_instr and decomp_instr:
                                opname_o = getattr(orig_instr, 'opname', str(orig_instr))
                                opname_d = getattr(decomp_instr, 'opname', str(decomp_instr))
                                pattern = f"{opname_o} -> {opname_d}"
                                pattern_counter[pattern] += 1
                            elif orig_instr and not decomp_instr:
                                opname_o = getattr(orig_instr, 'opname', str(orig_instr))
                                pattern_counter[f"{opname_o} -> MISSING"] += 1
                            elif decomp_instr and not orig_instr:
                                opname_d = getattr(decomp_instr, 'opname', str(decomp_instr))
                                pattern_counter[f"EXTRA -> {opname_d}"] += 1
    except Exception as e:
        print(f"  ERROR {pyc_path}: {e}")

print(f"\nTotal mismatched functions in top 20: {total_mismatch}")
print(f"\nTop 30 failure patterns:")
for pattern, count in pattern_counter.most_common(30):
    print(f"  {count:4d}  {pattern}")
