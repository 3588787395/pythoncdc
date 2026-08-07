#!/usr/bin/env python3
"""Deep analysis of repro_01: try-except return value loss."""
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

# Load repro_01
pyc_path = ".trae/specs/region-comment-multi-pyc-iteration/rounds/round_45/test_engineer/minimal_repros/repro_01_try_except_return.pyc"
ok_path = ".trae/specs/region-comment-multi-pyc-iteration/rounds/round_45/test_engineer/minimal_repros/repro_01_try_except_returnOK.py"

orig_code = load_pyc_code(pyc_path)
orig_map = extract_code_objects(orig_code)

with open(ok_path, 'r', encoding='utf-8') as f:
    decomp_source = f.read()

print("=== Decompiled source ===")
print(decomp_source)
print()

# Compile decompiled
cfile = py_compile.compile(ok_path, doraise=True, quiet=2)
with open(cfile, 'rb') as f:
    f.read(16)
    decomp_code = marshal.load(f)

decomp_map = extract_code_objects(decomp_code)

# Compare each function
for name in sorted(set(orig_map.keys()) & set(decomp_map.keys())):
    cmp = compare_bytecode(orig_map[name], decomp_map[name])
    if cmp.get('match') or cmp.get('jump_only'):
        print(f"  {name}: MATCHED")
        continue

    print(f"\n=== {name} ===")
    print(f"  Match: {cmp.get('match')}, Jump-only: {cmp.get('jump_only')}")
    print(f"  Orig count: {cmp.get('orig_count')}, Decomp count: {cmp.get('decomp_count')}")

    true_diffs = cmp.get('true_diffs', [])
    print(f"  True diffs ({len(true_diffs)}):")
    for td in true_diffs:
        print(f"    idx={td.get('index')}: {td.get('orig_op','?')}({td.get('orig_arg','?')}) -> {td.get('decomp_op','?')}({td.get('decomp_arg','?')})  type={td.get('type','')}")

    print(f"\n  ORIG bytecode:")
    for i, instr in enumerate(dis.get_instructions(orig_map[name])):
        print(f"    {i:3d}  {instr.opname:30s} {instr.argval}")

    print(f"\n  DECOMP bytecode:")
    for i, instr in enumerate(dis.get_instructions(decomp_map[name])):
        print(f"    {i:3d}  {instr.opname:30s} {instr.argval}")

# Also analyze repro_02
print("\n\n=== repro_02_try_except_finally ===")
pyc_path2 = ".trae/specs/region-comment-multi-pyc-iteration/rounds/round_45/test_engineer/minimal_repros/repro_02_try_except_finally.pyc"
ok_path2 = ".trae/specs/region-comment-multi-pyc-iteration/rounds/round_45/test_engineer/minimal_repros/repro_02_try_except_finallyOK.py"

orig_code2 = load_pyc_code(pyc_path2)
orig_map2 = extract_code_objects(orig_code2)

with open(ok_path2, 'r', encoding='utf-8') as f:
    decomp_source2 = f.read()

print("Decompiled source:")
print(decomp_source2)

cfile2 = py_compile.compile(ok_path2, doraise=True, quiet=2)
with open(cfile2, 'rb') as f:
    f.read(16)
    decomp_code2 = marshal.load(f)

decomp_map2 = extract_code_objects(decomp_code2)

for name in sorted(set(orig_map2.keys()) & set(decomp_map2.keys())):
    cmp = compare_bytecode(orig_map2[name], decomp_map2[name])
    if cmp.get('match') or cmp.get('jump_only'):
        print(f"  {name}: MATCHED")
        continue

    print(f"\n=== {name} ===")
    true_diffs = cmp.get('true_diffs', [])
    print(f"  True diffs ({len(true_diffs)}):")
    for td in true_diffs:
        print(f"    idx={td.get('index')}: {td.get('orig_op','?')}({td.get('orig_arg','?')}) -> {td.get('decomp_op','?')}({td.get('decomp_arg','?')})  type={td.get('type','')}")

    print(f"\n  ORIG bytecode:")
    for i, instr in enumerate(dis.get_instructions(orig_map2[name])):
        print(f"    {i:3d}  {instr.opname:30s} {instr.argval}")

    print(f"\n  DECOMP bytecode:")
    for i, instr in enumerate(dis.get_instructions(decomp_map2[name])):
        print(f"    {i:3d}  {instr.opname:30s} {instr.argval}")
