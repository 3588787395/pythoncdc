#!/usr/bin/env python3
"""Deep analysis of trade_live_broker.pyc mismatches - find root cause of LOAD_GLOBAL->LOAD_FAST pattern."""
import sys
import os
import marshal
import py_compile
import types
import dis
from pathlib import Path

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

pyc_path = "site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc"
ok_py_path = pyc_path.replace('.pyc', 'OK.py')

# Decompile
source = decompile_pyc(pyc_path)
with open(ok_py_path, 'w', encoding='utf-8') as f:
    f.write(source)

# Load and compare
orig_code = load_pyc_code(pyc_path)
cfile = py_compile.compile(ok_py_path, doraise=True, quiet=2)
with open(cfile, 'rb') as f:
    f.read(16)
    decomp_code = marshal.load(f)

orig_map = extract_code_objects(orig_code)
decomp_map = extract_code_objects(decomp_code)
common = set(orig_map.keys()) & set(decomp_map.keys())

mismatch_details = []
for name in sorted(common):
    cmp = compare_bytecode(orig_map[name], decomp_map[name])
    if cmp.get('match') or cmp.get('jump_only'):
        continue
    true_diffs = cmp.get('true_diffs', [])
    if not true_diffs:
        continue
    td = true_diffs[0]
    mismatch_details.append({
        'name': name,
        'orig_op': td.get('orig_op', '?'),
        'decomp_op': td.get('decomp_op', '?'),
        'orig_arg': td.get('orig_arg', '?'),
        'decomp_arg': td.get('decomp_arg', '?'),
        'true_diffs_count': len(true_diffs),
        'jump_diffs_count': len(cmp.get('jump_diffs', [])),
        'orig_count': cmp.get('orig_count', 0),
        'decomp_count': cmp.get('decomp_count', 0),
    })

# Group by first diff pattern
from collections import Counter
pattern_groups = Counter()
for m in mismatch_details:
    pattern_groups[f"{m['orig_op']} -> {m['decomp_op']}"] += 1

print(f"Total mismatches: {len(mismatch_details)}")
print("\nPattern groups:")
for pat, cnt in pattern_groups.most_common(20):
    print(f"  {cnt:3d}  {pat}")

# Show details for top 3 patterns
print("\n=== Detailed mismatches (top 15) ===")
for m in mismatch_details[:15]:
    print(f"\n  Function: {m['name']}")
    print(f"  First diff: {m['orig_op']}({m['orig_arg']}) -> {m['decomp_op']}({m['decomp_arg']})")
    print(f"  True diffs: {m['true_diffs_count']}, Jump diffs: {m['jump_diffs_count']}")
    print(f"  Orig instrs: {m['orig_count']}, Decomp instrs: {m['decomp_count']}")

# For the top 3 mismatched functions, show full bytecode
print("\n=== Full bytecode for top 3 mismatched functions ===")
for m in mismatch_details[:3]:
    name = m['name']
    print(f"\n--- {name} ---")
    print(f"  ORIG ({m['orig_count']} instrs):")
    for i, instr in enumerate(dis.get_instructions(orig_map[name])):
        print(f"    {i:3d}  {instr.opname:30s} {instr.argval}")
    print(f"  DECOMP ({m['decomp_count']} instrs):")
    for i, instr in enumerate(dis.get_instructions(decomp_map[name])):
        print(f"    {i:3d}  {instr.opname:30s} {instr.argval}")
