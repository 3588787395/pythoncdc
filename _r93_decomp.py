#!/usr/bin/env python3
"""R93 check: full decompiled source of get_multiminute_his_data"""
import sys
sys.path.insert(0, '.')
from pycdc import decompile_pyc

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
decomp_src = decompile_pyc(target_pyc)
lines = decomp_src.split('\n')
in_func = False
func_lines = []
for i, line in enumerate(lines):
    if 'def get_multiminute_his_data' in line:
        in_func = True
    if in_func:
        func_lines.append((i+1, line))
        # Stop at next function def
        if i > 0 and line and not line.startswith(' ') and not line.startswith('\t') and 'def ' in line and 'get_multiminute_his_data' not in line:
            break
        if len(func_lines) > 80:
            break

for lineno, line in func_lines:
    print(f"{lineno:4d}: {line}")
