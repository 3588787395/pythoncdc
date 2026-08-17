#!/usr/bin/env python3
"""R90 查看实际反编译输出"""
import sys, os, marshal, types
sys.path.insert(0, '.')
from pycdc import decompile_pyc as _pycdc_decompile

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
with open(target_pyc, 'rb') as f:
    f.read(16)
    orig_code = marshal.loads(f.read())

# Decompile
result = _pycdc_decompile(target_pyc)
if result:
    lines = result.split('\n')
    # Find get_kline_by_count_new function
    in_func = False
    func_lines = []
    for line in lines:
        if 'def get_kline_by_count_new' in line:
            in_func = True
        if in_func:
            func_lines.append(line)
            if len(func_lines) > 1 and line.strip() and not line.startswith(' ') and not line.startswith('\t') and 'def ' not in line:
                break
            if len(func_lines) > 60:
                break
    print('\n'.join(func_lines[:50]))
else:
    print("Decompilation failed!")
