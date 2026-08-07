#!/usr/bin/env python3
"""R36 test: decompile trade_schedule.pyc and check specific functions."""

import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from pycdc import decompile_pyc

PYC_PATH = os.path.join(HERE, 'site-packages', 'IQData', 'utils', 'trade_schedule.pyc')

source = decompile_pyc(PYC_PATH)

# Write full output
with open('_r36_trade_schedule_out.py', 'w', encoding='utf-8') as f:
    f.write(source)

# Extract specific functions
def extract_func(lines, func_name):
    in_func = False
    func_lines = []
    func_indent = 0
    for i, line in enumerate(lines):
        if f'def {func_name}' in line:
            in_func = True
            func_indent = len(line) - len(line.lstrip())
            func_lines.append(line)
            continue
        if in_func:
            if line.strip() == '':
                func_lines.append(line)
                continue
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= func_indent and line.strip() and not line.strip().startswith('#'):
                break
            func_lines.append(line)
    return func_lines

lines = source.split('\n')

results = []
for fname in ['is_stock_trade_time_now', 'get_trading_schedule', 'get_trading_time_tuple', 'is_stock_trade_trigger']:
    func_lines = extract_func(lines, fname)
    results.append(f"=== {fname} ===")
    results.extend(func_lines)
    results.append("=== END ===")
    results.append("")

with open('_r36_func_output.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print("Done. Output written to _r36_func_output.txt")
