#!/usr/bin/env python3
"""Find first not-ok pyc alphabetically and analyze its mismatches."""
import json
import sys
import os
import marshal
import py_compile
import types
import dis
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))

from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode

def load_pyc_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def extract_code_objects(code_obj, prefix=""):
    result = {}
    name = prefix + code_obj.co_name if prefix else (code_obj.co_name or '<module>')
    result[name] = code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            child_prefix = (prefix + code_obj.co_name + ".") if prefix else (code_obj.co_name + ".")
            result.update(extract_code_objects(const, child_prefix))
    return result

idx = json.load(open('pyc_index.json', encoding='utf-8'))
not_ok = sorted([e for e in idx if e['decompile_status'] != 'ok'], key=lambda e: e['path'])
print(f"First 5 not-ok pyc files (alphabetical):")
for e in not_ok[:5]:
    print(f"  {e['path']}: {e['decompile_status']} rate={e['bytecode_match_rate']:.4f}")

# Analyze the first not-ok pyc
target = not_ok[0]
pyc_path = target['path']
ok_py_path = pyc_path.replace('.pyc', 'OK.py')
print(f"\n=== Analyzing: {os.path.basename(pyc_path)} ===")

source = decompile_pyc(pyc_path)
with open(ok_py_path, 'w', encoding='utf-8') as f:
    f.write(source)

orig_code = load_pyc_code(pyc_path)
try:
    cfile = py_compile.compile(ok_py_path, doraise=True, quiet=2)
    with open(cfile, 'rb') as f:
        f.read(16)
        decomp_code = marshal.load(f)
except Exception as e:
    print(f"COMPILE ERROR: {e}")
    sys.exit(1)

orig_map = extract_code_objects(orig_code)
decomp_map = extract_code_objects(decomp_code)
common = set(orig_map.keys()) & set(decomp_map.keys())

mismatches = []
for name in sorted(common):
    cmp = compare_bytecode(orig_map[name], decomp_map[name])
    if cmp.get('match') or cmp.get('jump_only'):
        continue
    true_diffs = cmp.get('true_diffs', [])
    if not true_diffs:
        continue
    td = true_diffs[0]
    mismatches.append({
        'name': name,
        'orig_op': td.get('orig_op', '?'),
        'decomp_op': td.get('decomp_op', '?'),
        'orig_arg': td.get('orig_arg', '?'),
        'decomp_arg': td.get('decomp_arg', '?'),
        'true_diffs': true_diffs[:5],
        'true_diffs_count': len(true_diffs),
        'jump_diffs_count': len(cmp.get('jump_diffs', [])),
        'orig_count': cmp.get('orig_count', 0),
        'decomp_count': cmp.get('decomp_count', 0),
    })

print(f"Total functions: {len(orig_map)}, Matched: {len(orig_map) - len(mismatches)}, Mismatches: {len(mismatches)}")

# Show all mismatches
for m in mismatches:
    print(f"\n  Function: {m['name']}")
    print(f"  First diff: {m['orig_op']}({m['orig_arg']}) -> {m['decomp_op']}({m['decomp_arg']})")
    print(f"  True diffs: {m['true_diffs_count']}, Jump diffs: {m['jump_diffs_count']}")
    print(f"  Orig instrs: {m['orig_count']}, Decomp instrs: {m['decomp_count']}")

# Show full bytecode for the simplest mismatch (fewest true_diffs)
if mismatches:
    simplest = min(mismatches, key=lambda m: m['true_diffs_count'])
    name = simplest['name']
    print(f"\n=== Full bytecode for simplest mismatch: {name} ===")
    print(f"  ORIG ({simplest['orig_count']} instrs):")
    for i, instr in enumerate(dis.get_instructions(orig_map[name])):
        print(f"    {i:3d}  {instr.opname:30s} {instr.argval}")
    print(f"  DECOMP ({simplest['decomp_count']} instrs):")
    for i, instr in enumerate(dis.get_instructions(decomp_map[name])):
        print(f"    {i:3d}  {instr.opname:30s} {instr.argval}")
