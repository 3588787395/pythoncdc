#!/usr/bin/env python3
"""R91 extract and compile decompiled source for get_price_common"""
import sys, dis, marshal, types
sys.path.insert(0, '.')
from pycdc import decompile_pyc

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
decomp_src = decompile_pyc(target_pyc)

# Find get_price_common function in decompiled source
lines = decomp_src.split('\n')
in_func = False
func_lines = []
brace_depth = 0
for i, line in enumerate(lines):
    if 'def get_price_common' in line:
        in_func = True
    if in_func:
        func_lines.append(line)
        # Stop at next top-level def or class
        if i > 0 and line and not line.startswith(' ') and not line.startswith('\t') and 'def ' not in line and 'class ' not in line and line.strip():
            break
        if len(func_lines) > 200:
            break

func_src = '\n'.join(func_lines)
# Print first 80 lines
for i, line in enumerate(func_lines[:80]):
    print(f"{i+1:4d}: {line}")
