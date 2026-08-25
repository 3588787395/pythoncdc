#!/usr/bin/env python3
"""R100: Test fix and see decompiled output"""
import sys, marshal, dis, types, ast
sys.path.insert(0, '.')
import pycdc
from testqouter.round1.base import compare_bytecode

pyc_path = 'site-packages/IQCommon/api/check_strategy.pyc'
decompiled = pycdc.decompile_pyc(pyc_path)

# Find check_strategy function
lines = decompiled.split('\n')
in_func = False
for i, line in enumerate(lines):
    if 'def check_strategy' in line:
        in_func = True
    if in_func:
        print(f'{i+1:4d}: {line}')
    if in_func and i > 60:
        break
