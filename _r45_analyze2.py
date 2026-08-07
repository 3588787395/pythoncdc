#!/usr/bin/env python3
"""Analyze failure patterns across partial pyc files using compare_bytecode directly."""
import json
import sys
import os
import marshal
import py_compile
import types
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))

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

idx = json.load(open('pyc_index.json', encoding='utf-8'))
partial = [e for e in idx if e['decompile_status'] == 'partial']
partial.sort(key=lambda e: e.get('function_count', 0) * (1 - e['bytecode_match_rate']), reverse=True)

pattern_counter = Counter()
first_diff_counter = Counter()
total_mismatch_funcs = 0
detail_list = []

for entry in partial[:30]:
    pyc_path = entry['path']
    ok_py_path = pyc_path.replace('.pyc', 'OK.py')

    try:
        source = decompile_pyc(pyc_path)
        if source is None:
            print(f"  DECOMPILE NULL: {os.path.basename(pyc_path)}")
            continue
        with open(ok_py_path, 'w', encoding='utf-8') as f:
            f.write(source)
    except Exception as e:
        print(f"  DECOMPILE ERR: {os.path.basename(pyc_path)}: {e}")
        continue

    try:
        orig_code = load_pyc_code(pyc_path)
    except Exception as e:
        print(f"  LOAD ERR: {os.path.basename(pyc_path)}: {e}")
        continue

    try:
        cfile = py_compile.compile(ok_py_path, doraise=True, quiet=2)
        with open(cfile, 'rb') as f:
            f.read(16)
            decomp_code = marshal.load(f)
    except Exception as e:
        print(f"  COMPILE ERR: {os.path.basename(pyc_path)}: {e}")
        continue

    orig_map = extract_code_objects(orig_code)
    decomp_map = extract_code_objects(decomp_code)
    common = set(orig_map.keys()) & set(decomp_map.keys())

    matched = 0
    mismatch_count = 0
    for name in sorted(common):
        cmp = compare_bytecode(orig_map[name], decomp_map[name])
        if cmp.get('match') or cmp.get('jump_only'):
            matched += 1
        else:
            mismatch_count += 1
            total_mismatch_funcs += 1
            true_diffs = cmp.get('true_diffs', [])
            if true_diffs:
                td = true_diffs[0]
                orig_op = td.get('orig_op', '?')
                decomp_op = td.get('decomp_op', '?')
                orig_arg = str(td.get('orig_arg', '?'))[:30]
                decomp_arg = str(td.get('decomp_arg', '?'))[:30]
                first_diff_str = f"{orig_op} -> {decomp_op}  ({orig_arg} vs {decomp_arg})"
                first_diff_counter[first_diff_str[:100]] += 1

                # Count patterns
                for td2 in true_diffs[:3]:
                    o = td2.get('orig_op', '?')
                    d = td2.get('decomp_op', '?')
                    if o != '?' and d != '?':
                        pattern_counter[f"{o} -> {d}"] += 1
                    elif o != '?':
                        pattern_counter[f"{o} -> MISSING"] += 1
                    elif d != '?':
                        pattern_counter[f"EXTRA -> {d}"] += 1

    detail_list.append({
        'path': os.path.basename(pyc_path),
        'total': len(orig_map),
        'matched': matched,
        'mismatch_count': mismatch_count,
    })

print("=== Top 30 partial files analyzed ===")
print(f"Total mismatched functions: {total_mismatch_funcs}")
print()
print("File details (sorted by impact):")
for d in detail_list:
    rate = d['matched'] / d['total'] if d['total'] > 0 else 0
    print(f"  {d['path']:50s}  {d['matched']}/{d['total']} = {rate:.2%}  ({d['mismatch_count']} mismatches)")

print()
print("Top 25 first_diff patterns:")
for pat, cnt in first_diff_counter.most_common(25):
    print(f"  {cnt:4d}  {pat}")

print()
print("Top 25 opcode transition patterns:")
for pat, cnt in pattern_counter.most_common(25):
    print(f"  {cnt:4d}  {pat}")
