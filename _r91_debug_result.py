#!/usr/bin/env python3
"""R91 debug result structure"""
import sys, json
sys.path.insert(0, '.')
from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
decomp_src = decompile_pyc(target_pyc)
result = compare_bytecode(target_pyc, decomp_src)

print(f"Type: {type(result)}")
print(f"Keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
if isinstance(result, dict):
    for k, v in result.items():
        if k == 'functions':
            print(f"  functions type: {type(v)}")
            if isinstance(v, dict):
                print(f"  function keys: {list(v.keys())[:5]}")
            elif isinstance(v, list):
                print(f"  function count: {len(v)}")
                if v:
                    print(f"  first item: {v[0]}")
        else:
            print(f"  {k}: {v}")
