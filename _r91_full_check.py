#!/usr/bin/env python3
"""Check full match status"""
import sys
sys.path.insert(0, '.')
from testqouter.round1.base import compare_bytecode

result = compare_bytecode("site-packages/IQCommon/api/klinedata.pyc")
functions = result.get('functions', {})
for name, data in sorted(functions.items(), key=lambda x: x[1].get('true_diffs', 0), reverse=True):
    td = data.get('true_diffs', 0)
    jd = data.get('jump_diffs', 0)
    match = data.get('match', False)
    status = "OK" if match else "FAIL"
    print(f"  {status:4s} {td:5d} true, {jd:4d} jump - {name}")
