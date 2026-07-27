"""分析多个失败函数的源码差异"""
import sys
import re

SRC = '/tmp/r23_decompiled.py'

with open(SRC, 'r') as f:
    src = f.read()

# 失败函数列表
funcs = ['api_get', 'balance_statement', 'get_holiday_online', 'load_get_exrights',
         'get_str_data', 'valuation', 'valuation_new', 'get_option_info',
         'get_price', 'get_date_and_count', 'change_his_to_backward']

for name in funcs:
    print(f"\n{'='*80}\n# Function: {name}\n{'='*80}")
    match = re.search(rf'def {name}\(.*?\n(?=\ndef |\Z|@)', src, re.DOTALL)
    if match:
        print(match.group(0))
    else:
        print(f"未找到 {name}")
