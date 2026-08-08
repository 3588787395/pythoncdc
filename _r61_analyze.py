#!/usr/bin/env python3
"""R61: Analyze load_from_kwargs bytecode mismatch - compile OK.py directly"""
import dis
import marshal
import sys
import py_compile
import os
from pathlib import Path

pyc_path = Path("site-packages/IQEngine/plugins/plugin_system_accounts/position_model/live_future_position.pyc")
ok_py_path = Path("site-packages/IQEngine/plugins/plugin_system_accounts/position_model/live_future_positionOK.py")

# Load original code object from .pyc
with open(pyc_path, 'rb') as f:
    magic = f.read(4)
    flags = int.from_bytes(f.read(4), 'little')
    if flags & 0x1:
        f.read(8)
    else:
        f.read(8)
    code = marshal.load(f)

# Find load_from_kwargs in original
def find_code_obj(code, name):
    if code.co_name == name:
        return code
    for const in code.co_consts:
        if hasattr(const, 'co_name'):
            result = find_code_obj(const, name)
            if result:
                return result
    return None

orig_func = find_code_obj(code, 'load_from_kwargs')
print("=== ORIGINAL load_from_kwargs bytecode ===")
for i, instr in enumerate(dis.get_instructions(orig_func)):
    print(f"  {i:3d} {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")

# Compile OK.py to get decompiled bytecode
with open(ok_py_path, 'r', encoding='utf-8') as f:
    source = f.read()
decomp_code = compile(source, str(ok_py_path), 'exec')

decomp_func = find_code_obj(decomp_code, 'load_from_kwargs')
if decomp_func:
    print("\n=== DECOMPILED load_from_kwargs bytecode ===")
    for i, instr in enumerate(dis.get_instructions(decomp_func)):
        print(f"  {i:3d} {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
else:
    print("load_from_kwargs not found in decompiled code!")
    # List all code objects
    def list_code_objs(code, prefix=""):
        for const in code.co_consts:
            if hasattr(const, 'co_name'):
                print(f"  {prefix}{const.co_name}")
                list_code_objs(const, prefix + "  ")
    print("Available code objects:")
    list_code_objs(decomp_code)
