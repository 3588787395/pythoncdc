import sys, os
sys.path.insert(0, '.')
from pycdc import decompile_pyc

pyc_path = 'site-packages/IQCommon/api/klinedata.pyc'
source = decompile_pyc(pyc_path)

# Find get_kline_by_date_new function
lines = source.split('\n')
in_func = False
func_lines = []
brace_depth = 0

for i, line in enumerate(lines):
    if 'def get_kline_by_date_new' in line:
        in_func = True
    if in_func:
        func_lines.append(f"{i}: {line}")
        # End when we hit the next def at same indent level
        if len(func_lines) > 5 and line.strip().startswith('def ') and 'get_kline_by_date_new' not in line:
            func_lines.pop()  # remove the next def
            break

print('\n'.join(func_lines[:80]))
