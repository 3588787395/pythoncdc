#!/usr/bin/env python3
"""Disassemble get_trading_schedule bytecode and compare with decompiled."""

import sys, os, marshal, types, dis

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

PYC_PATH = os.path.join(HERE, 'site-packages', 'IQData', 'utils', 'trade_schedule.pyc')

with open(PYC_PATH, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

# Find get_trading_schedule
def find_code(code_obj, name):
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            sub = find_code(const, name)
            if sub:
                return sub
    return None

gts = find_code(code, 'get_trading_schedule')
print("=== Original get_trading_schedule bytecode ===")
dis.dis(gts)
print()

# Now compile the decompiled output and compare
from pycdc import decompile_pyc
source = decompile_pyc(PYC_PATH)

# Compile the decompiled source
try:
    decompiled_code = compile(source, '<decompiled>', 'exec')
    gts2 = find_code(decompiled_code, 'get_trading_schedule')
    if gts2:
        print("=== Decompiled get_trading_schedule bytecode ===")
        dis.dis(gts2)
except SyntaxError as e:
    print(f"SyntaxError: {e}")

# Now compile the reference OK source
ref_path = os.path.join(HERE, 'site-packages', 'IQData', 'utils', 'trade_scheduleOK.py')
with open(ref_path, 'r', encoding='utf-8') as f:
    ref_source = f.read()
# Remove header comments
lines = ref_source.split('\n')
start = 0
for i, line in enumerate(lines):
    if line.startswith('from ') or line.startswith('STOCK') or line.startswith('FUTURE') or line.startswith('@') or line.startswith('def '):
        start = i
        break
ref_source = '\n'.join(lines[start:])

try:
    ref_code = compile(ref_source, '<reference>', 'exec')
    gts3 = find_code(ref_code, 'get_trading_schedule')
    if gts3:
        print("=== Reference get_trading_schedule bytecode ===")
        dis.dis(gts3)
except SyntaxError as e:
    print(f"SyntaxError in reference: {e}")
