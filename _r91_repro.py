#!/usr/bin/env python3
"""R91 minimal reproduction: if-elif chain with merge_block in elif_bodies"""
import sys, dis, types

# Source that represents the original bytecode pattern
src = '''
def test(a, b, c, d):
    if a:
        if b:
            return None
        elif c:
            return None
        elif d:
            return None
    elif b:
        if c:
            return None
        elif d:
            return None
    else:
        if d:
            return None
    x = 1
    return x
'''

# Compile and check
code = compile(src, '<test>', 'exec')
for const in code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'test':
        print("=== Expected bytecode ===")
        for instr in dis.get_instructions(const):
            if instr.offset < 100:
                print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
        break

# Now decompile and compare
sys.path.insert(0, '.')
from core.cfg.region_ast_generator import generate_ast_from_regions
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
import marshal

# Write a test pyc
with open('_r91_repro.pyc', 'wb') as f:
    f.write(b'\x6f\x0d\x0d\x0a' + b'\x00' * 12)  # header
    marshal.dump(code, f)

from pycdc import decompile_pyc
decomp_src = decompile_pyc('_r91_repro.pyc')
print("\n=== Decompiled source ===")
print(decomp_src)

# Compile decompiled source and compare bytecode
decomp_code = compile(decomp_src, '<decompiled>', 'exec')
for const in decomp_code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'test':
        print("\n=== Decompiled bytecode ===")
        for instr in dis.get_instructions(const):
            if instr.offset < 100:
                print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
        break
