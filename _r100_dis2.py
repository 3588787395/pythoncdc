#!/usr/bin/env python3
"""R100: Detailed bytecode analysis of the chained compare region"""
import sys, marshal, dis, types
sys.path.insert(0, '.')

pyc_path = 'site-packages/IQCommon/api/check_strategy.pyc'
code = marshal.loads(open(pyc_path, 'rb').read()[16:])
funcs = [c for c in code.co_consts if isinstance(c, types.CodeType)]
cs = [f for f in funcs if f.co_name == 'check_strategy'][0]

# Print instructions around the problematic area (offset 794-850)
print('=== Key bytecode region (offset 794-1080) ===')
for instr in dis.get_instructions(cs):
    if 794 <= instr.offset <= 1080:
        print(f'  {instr.offset:4d} {instr.opname:30s} {instr.argval}')

# Also print the decompiled source to compare
import pycdc
decompiled = pycdc.decompile_pyc(pyc_path)
# Find the check_strategy function in the decompiled source
lines = decompiled.split('\n')
in_func = False
for i, line in enumerate(lines):
    if 'def check_strategy' in line:
        in_func = True
    if in_func:
        print(f'{i+1:4d}: {line}')
    if in_func and line.strip().startswith('return') and i > 100:
        break
