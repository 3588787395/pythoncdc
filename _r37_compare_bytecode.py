#!/usr/bin/env python3
import dis
import marshal
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

def load_pyc_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)  # skip header
        return marshal.load(f)

def find_code(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if hasattr(c, 'co_code'):
            r = find_code(c, name)
            if r:
                return r
    return None

def compare_bytecodes(orig_code, recompiled_code, func_name):
    orig_instrs = list(dis.get_instructions(orig_code))
    recomp_instrs = list(dis.get_instructions(recompiled_code))

    print(f"\n=== {func_name} ===")
    print(f"Original:    {len(orig_instrs)} instructions")
    print(f"Recompiled:  {len(recomp_instrs)} instructions")
    print(f"Diff:        {len(orig_instrs) - len(recomp_instrs)} instructions lost")

    if len(orig_instrs) != len(recomp_instrs):
        print("\n--- First 50 original instructions ---")
        for i, ins in enumerate(orig_instrs[:50]):
            print(f"{i:3d}: offset={ins.offset:4d} {ins.opname:30s} {ins.arg}")

        print("\n--- First 50 recompiled instructions ---")
        for i, ins in enumerate(recomp_instrs[:50]):
            print(f"{i:3d}: offset={ins.offset:4d} {ins.opname:30s} {ins.arg}")

        # Find where they diverge
        print("\n--- Finding divergence point ---")
        min_len = min(len(orig_instrs), len(recomp_instrs))
        divergence = None
        for i in range(min_len):
            orig_op = orig_instrs[i].opname
            recomp_op = recomp_instrs[i].opname
            if orig_op != recomp_op:
                divergence = i
                print(f"Divergence at index {i}:")
                print(f"  Original:    {orig_op} (offset={orig_instrs[i].offset})")
                print(f"  Recompiled:  {recomp_op} (offset={recomp_instrs[i].offset})")
                break

        if divergence:
            print(f"\n--- Context around divergence (±10) ---")
            start = max(0, divergence - 10)
            end = min(min_len, divergence + 10)
            for i in range(start, end):
                orig = orig_instrs[i] if i < len(orig_instrs) else None
                recomp = recomp_instrs[i] if i < len(recomp_instrs) else None
                marker = " >>>" if i == divergence else "    "
                orig_arg = orig.arg if orig else None
                recomp_arg = recomp.arg if recomp else None
                if orig and recomp:
                    print(f"{marker} {i:3d}: {orig.opname:30s} {orig_arg:10} | {recomp.opname:30s} {recomp_arg:10}")
                elif orig:
                    print(f"{marker} {i:3d}: {orig.opname:30s} {orig_arg:10} | (MISSING in recompiled)")
                elif recomp:
                    print(f"{marker} {i:3d}: (MISSING in original) | {recomp.opname:30s} {recomp_arg:10}")

# Main
pyc_path = "site-packages/fly/simtradding/pboxAccount_jupyterhub.pyc"
py_path = "site-packages/fly/simtradding/pboxAccount_jupyterhubOK.py"

orig_code = load_pyc_code(pyc_path)

with open(py_path, 'r', encoding='utf-8') as f:
    recompiled_code = compile(f.read(), py_path, 'exec')

for func_name in ['getPboxAccount', 'getVaildAccount']:
    orig_func = find_code(orig_code, func_name)
    recomp_func = find_code(recompiled_code, func_name)

    if orig_func and recomp_func:
        compare_bytecodes(orig_func, recomp_func, func_name)
    else:
        print(f"\n--- {func_name}: not found ---")