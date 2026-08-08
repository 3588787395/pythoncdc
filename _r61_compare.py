#!/usr/bin/env python3
"""R61: Compare original and decompiled bytecode for load_from_kwargs"""
import dis
import marshal
from pathlib import Path

pyc_path = Path("site-packages/IQEngine/plugins/plugin_system_accounts/position_model/live_future_position.pyc")
ok_py_path = Path("site-packages/IQEngine/plugins/plugin_system_accounts/position_model/live_future_positionOK.py")

# Load original
with open(pyc_path, 'rb') as f:
    f.read(4); f.read(4); f.read(8)
    code = marshal.load(f)

def find_code(code, name):
    if code.co_name == name:
        return code
    for const in code.co_consts:
        if hasattr(const, 'co_name'):
            result = find_code(const, name)
            if result:
                return result
    return None

orig_func = find_code(code, 'load_from_kwargs')

# Compile decompiled
with open(ok_py_path, 'r', encoding='utf-8') as f:
    source = f.read()
decomp_code = compile(source, str(ok_py_path), 'exec')
decomp_func = find_code(decomp_code, 'load_from_kwargs')

# Print side by side from index 50
print("=== ORIGINAL (from index 48) ===")
for i, instr in enumerate(dis.get_instructions(orig_func)):
    if i >= 48:
        print(f"  {i:3d} {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")

print("\n=== DECOMPILED (from index 48) ===")
for i, instr in enumerate(dis.get_instructions(decomp_func)):
    if i >= 48:
        print(f"  {i:3d} {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
