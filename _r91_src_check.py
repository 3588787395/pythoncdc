#!/usr/bin/env python3
"""R91 check what Python compiler generates for this source"""
import sys, dis
sys.path.insert(0, '.')
from pycdc import decompile_pyc

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
decomp_src = decompile_pyc(target_pyc)

# Compile and check bytecode around offset 278
decomp_code = compile(decomp_src, '<decompiled>', 'exec')
import types
for const in decomp_code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'get_price_common':
        print("Decompiled bytecode around offset 260-290:")
        for instr in dis.get_instructions(const):
            if 260 <= instr.offset <= 300:
                print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
        
        # Also show source lines around the issue
        print("\nSource lines:")
        lines = decomp_src.split('\n')
        in_func = False
        for i, line in enumerate(lines):
            if 'def get_price_common' in line:
                in_func = True
            if in_func:
                print(f"  {i+1:4d}: {line}")
                if i > 0 and line.strip() and not line.startswith(' ') and 'def ' not in line:
                    break
                if i > 60:
                    break
        break
