"""R22 测试工程师：dump 反编译源码中失败函数的实际内容"""
import sys
import ast

SRC = '/tmp/r22_decompiled.py'

TARGETS = ['get_quote', 'convert_to_list', 'get_holiday_online',
           'get_index_stocks', 'get_fundflow_day', 'get_block_stocks',
           'check_index_code', 'check_industry_code',
           'get_opt_contracts', 'get_opt_last_dates', 'get_opt_objects',
           'get_stock_exrights']

with open(SRC) as f:
    src = f.read()

tree = ast.parse(src)
src_text = {node.name: ast.unparse(node) for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}

for name in TARGETS:
    print(f"\n{'='*70}")
    print(f"=== {name} ===")
    if name in src_text:
        print(src_text[name])
    else:
        print("  [NOT FOUND in source]")
