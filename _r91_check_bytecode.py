#!/usr/bin/env python3
"""R91 check what the Python compiler generates for the decompiled source"""
import sys, dis, types
sys.path.insert(0, '.')
from pycdc import decompile_pyc

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
decomp_src = decompile_pyc(target_pyc)
decomp_code = compile(decomp_src, '<decompiled>', 'exec')

# Find get_price_common
for const in decomp_code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'get_price_common':
        func_code = const
        break

# Print bytecode around offset 278
print("Decompiled bytecode around offset 278:")
for instr in dis.get_instructions(func_code):
    if 250 <= instr.offset <= 300:
        print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
