#!/usr/bin/env python3
"""R91 view decompiled source with line numbers"""
import sys
sys.path.insert(0, '.')
from pycdc import decompile_pyc

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
result = decompile_pyc(target_pyc)
if result:
    lines = result.split('\n')
    in_func = False
    func_lines = []
    for line in lines:
        if 'def get_price_common' in line:
            in_func = True
        if in_func:
            func_lines.append(line)
            if len(func_lines) > 1 and line.strip() and not line.startswith(' ') and not line.startswith('\t') and 'def ' not in line:
                break
            if len(func_lines) > 50:
                break
    for i, line in enumerate(func_lines[:35]):
        print(f"{i+1:3d}: {repr(line)}")
