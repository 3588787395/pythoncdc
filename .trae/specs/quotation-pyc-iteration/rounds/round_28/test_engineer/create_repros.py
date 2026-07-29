"""R28 测试工程师：创建10+最小复现实例，验证IF_NONE/IF_NOT_NONE AND链识别问题"""
import os
import sys
import dis
import py_compile

sys.path.insert(0, '/workspace')

OUT_DIR = '/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_28/test_engineer/minimal_repros'
os.makedirs(OUT_DIR, exist_ok=True)

CASES = [
    ('repro_r28_01_and_is_not_none_and_is_none',
     'def f(start_year, end_year, params):\n    if start_year is not None and end_year is None:\n        params[\'start_year\'] = start_year\n    elif start_year is None and end_year is not None:\n        params[\'end_year\'] = end_year\n    elif start_year is not None and end_year is not None:\n        params[\'start_year\'] = start_year\n        params[\'end_year\'] = end_year\n'),
    ('repro_r28_02_and_none_chain_two_branches',
     'def f(a, b, params):\n    if a is not None and b is None:\n        params[\'a\'] = a\n    elif a is None and b is not None:\n        params[\'b\'] = b\n'),
    ('repro_r28_03_and_none_with_return',
     'def f(a, b):\n    if a is not None and b is None:\n        return 1\n    elif a is None and b is not None:\n        return 2\n    return 0\n'),
    ('repro_r28_04_and_none_three_branches',
     'def f(a, b, c, params):\n    if a is not None and b is None:\n        params[\'a\'] = a\n    elif a is None and c is not None:\n        params[\'c\'] = c\n    elif b is not None and c is None:\n        params[\'b\'] = b\n'),
    ('repro_r28_05_and_mixed_false_none',
     'def f(a, b):\n    if a and b is None:\n        return 1\n    return 0\n'),
    ('repro_r28_06_and_mixed_none_false',
     'def f(a, b):\n    if a is not None and b:\n        return 1\n    return 0\n'),
    ('repro_r28_07_and_none_in_if',
     'def f(a, b, params):\n    if a is not None and b is None:\n        params[\'x\'] = a\n'),
    ('repro_r28_08_and_none_elif_only',
     'def f(a, b):\n    if a:\n        return 0\n    elif a is not None and b is None:\n        return 1\n    return 2\n'),
    ('repro_r28_09_and_none_with_continue',
     'def f(items):\n    for i in items:\n        if i is not None and i > 0:\n            continue\n        return i\n    return None\n'),
    ('repro_r28_10_or_none_chain',
     'def f(a, b):\n    if a is None or b is None:\n        return 1\n    return 0\n'),
    ('repro_r28_11_or_not_none_chain',
     'def f(a, b):\n    if a is not None or b is not None:\n        return 1\n    return 0\n'),
    ('repro_r28_12_and_none_nested_in_while',
     'def f(a, b):\n    while True:\n        if a is not None and b is None:\n            return 1\n        elif a is None and b is not None:\n            return 2\n        break\n    return 0\n'),
    # R28-N2: 嵌套if-else模式（cash_collection_ability回归用例）
    # 两个IF_NOT_NONE跳转到不同目标（外层else vs 内层else），不是AND链
    ('repro_r28_13_nested_if_else_none',
     'def f(a, b, params):\n    if a is None:\n        if b is None:\n            params[\'x\'] = 1\n        else:\n            params[\'x\'] = 2\n    else:\n        if b is None:\n            params[\'x\'] = 3\n        else:\n            params[\'x\'] = 4\n'),
    ('repro_r28_14_nested_if_else_not_none',
     'def f(a, b, params):\n    if a is not None:\n        if b is not None:\n            params[\'x\'] = 1\n        else:\n            params[\'x\'] = 2\n    else:\n        if b is not None:\n            params[\'x\'] = 3\n        else:\n            params[\'x\'] = 4\n'),
    ('repro_r28_15_nested_if_none_else_not_none',
     'def f(a, b, params):\n    if a is None:\n        if b is not None:\n            params[\'x\'] = 1\n        else:\n            params[\'x\'] = 2\n    else:\n        if b is None:\n            params[\'x\'] = 3\n        else:\n            params[\'x\'] = 4\n'),
    ('repro_r28_16_nested_if_with_elif',
     'def f(a, b, params):\n    if a is None:\n        if b is None:\n            params[\'x\'] = 1\n        else:\n            params[\'x\'] = 2\n    elif b is None:\n        params[\'x\'] = 3\n    else:\n        params[\'x\'] = 4\n'),
]

for name, src in CASES:
    src_path = os.path.join(OUT_DIR, name + '.py')
    pyc_path = os.path.join(OUT_DIR, name + '.pyc')
    with open(src_path, 'w') as f:
        f.write(src)
    py_compile.compile(src_path, pyc_path, doraise=True)
    print(f"[created] {name}")

print(f"\n共创建 {len(CASES)} 个复现实例")
