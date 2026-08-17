#!/usr/bin/env python3
"""R91 check specific function match status"""
import sys, marshal, types, dis
sys.path.insert(0, '.')
from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
decomp_src = decompile_pyc(target_pyc)
result = compare_bytecode(target_pyc, decomp_src)
functions = result.get('functions', {})

# Check specific functions
for name in ['get_kline_by_count_new', 'get_all_real_minute_kline', 'klineCacheData_to_dict',
             'get_all_real_daily_kline', 'get_kline_by_date_ndarray', 'to_pd_result',
             'get_date_and_count', 'get_kline_by_count', 'get_multiminute_his_data_by_date',
             'stk_resample_days_bars']:
    if name in functions:
        data = functions[name]
        td = data.get('true_diffs', 0)
        jd = data.get('jump_diffs', 0)
        match = data.get('match', False)
        print(f"  {'OK' if match else 'FAIL':4s} {td:5d} true, {jd:4d} jump - {name}")
    else:
        print(f"  ????? {name} not found")
