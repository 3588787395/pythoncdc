#!/usr/bin/env python3
"""R91 list all function names"""
import sys
sys.path.insert(0, '.')
from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
decomp_src = decompile_pyc(target_pyc)
result = compare_bytecode(target_pyc, decomp_src)
functions = result.get('functions', {})

for name, data in sorted(functions.items()):
    td = data.get('true_diffs', 0)
    jd = data.get('jump_diffs', 0)
    match = data.get('match', False)
    print(f"  {'OK' if match else 'FAIL':4s} {td:5d} true, {jd:4d} jump - {name}")
