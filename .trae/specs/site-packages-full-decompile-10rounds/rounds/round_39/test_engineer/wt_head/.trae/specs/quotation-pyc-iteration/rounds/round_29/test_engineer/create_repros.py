"""R29 测试工程师：创建10+最小复现实例，验证if-elif chain merge_block吸收问题"""
import os
import sys
import py_compile

sys.path.insert(0, '/workspace')

OUT_DIR = '/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_29/test_engineer/minimal_repros'
os.makedirs(OUT_DIR, exist_ok=True)

CASES = [
    # 基本模式：if-elif chain后跟另一个if语句
    ('repro_r29_01_elif_then_if',
     'def f(x, y):\n    if x == 1:\n        y = 10\n    elif x == 2:\n        y = 20\n    elif x == 3:\n        y = 30\n    if y is None:\n        return 0\n    return y\n'),
    # if-elif chain后跟for循环
    ('repro_r29_02_elif_then_for',
     'def f(x, d):\n    if x == 1:\n        d = d[1]\n    elif x == 2:\n        d = d[2]\n    elif x == 3:\n        d = d[3]\n    result = []\n    for k in d:\n        result.extend(d[k])\n    return result\n'),
    # get_fields模式：if-elif chain + if not fields + for循环
    ('repro_r29_03_get_fields_pattern',
     'def f(fans, fields):\n    d = {1: 2, 3: 4}\n    if fans == 1:\n        d = d[1]\n    elif fans == 2:\n        d = d[2]\n    elif fans == 3:\n        d = d[3]\n    elif fans in d.keys():\n        d = d[fans]\n        if not fields:\n            return d\n        else:\n            return fields\n    if fields is None:\n        result = []\n        for k in d:\n            result.extend(d[k])\n        return result\n    return None\n'),
    # if-elif chain后跟赋值
    ('repro_r29_04_elif_then_assign',
     'def f(x):\n    if x == 1:\n        y = 10\n    elif x == 2:\n        y = 20\n    z = y + 1\n    return z\n'),
    # if-elif chain后跟return
    ('repro_r29_05_elif_then_return',
     'def f(x):\n    if x == 1:\n        y = 10\n    elif x == 2:\n        y = 20\n    return y\n'),
    # if-elif-else chain后跟if
    ('repro_r29_06_elif_else_then_if',
     'def f(x, y):\n    if x == 1:\n        y = 10\n    elif x == 2:\n        y = 20\n    else:\n        y = 30\n    if y > 15:\n        return 1\n    return 0\n'),
    # change_his_to_forward模式：嵌套if中的if-elif
    ('repro_r29_07_nested_elif_with_inner_if',
     'def f(a, b, c):\n    if a:\n        if b == 0:\n            c = 1\n        elif b == 1:\n            if c > 0:\n                return 1\n            else:\n                return 2\n        if c is None:\n            return 0\n    return c\n'),
    # build_future_fill_time模式：多层if-elif嵌套
    ('repro_r29_08_deep_elif_chain',
     'def f(x, y, z):\n    if x == 1:\n        if y == 1:\n            z = 10\n        elif y == 2:\n            z = 20\n        if z is None:\n            return 0\n    elif x == 2:\n        z = 30\n    return z\n'),
    # if-elif chain with return in last branch
    ('repro_r29_09_elif_return_last',
     'def f(x, d):\n    if x == 1:\n        d = d[1]\n    elif x == 2:\n        d = d[2]\n    elif x in d:\n        return d[x]\n    result = []\n    for k in d:\n        result.append(k)\n    return result\n'),
    # if-elif chain后跟while循环
    ('repro_r29_10_elif_then_while',
     'def f(x, items):\n    if x == 1:\n        items = items[1:]\n    elif x == 2:\n        items = items[2:]\n    i = 0\n    while i < len(items):\n        items[i] = items[i] + 1\n        i += 1\n    return items\n'),
    # Simple if-elif with merge starting a new block
    ('repro_r29_11_simple_elif_merge',
     'def f(x):\n    if x == 1:\n        x = 10\n    elif x == 2:\n        x = 20\n    if x > 15:\n        return 1\n    return 0\n'),
    # if-elif-elif with complex merge
    ('repro_r29_12_complex_elif_merge',
     'def f(x, y, z):\n    if x == 1:\n        y = 10\n    elif x == 2:\n        y = 20\n    elif x == 3:\n        y = 30\n    elif x == 4:\n        if z:\n            return z\n        return y\n    if y is None:\n        return 0\n    return y\n'),
]

for name, src in CASES:
    src_path = os.path.join(OUT_DIR, name + '.py')
    pyc_path = os.path.join(OUT_DIR, name + '.pyc')
    with open(src_path, 'w') as f:
        f.write(src)
    py_compile.compile(src_path, pyc_path, doraise=True)
    print(f"[created] {name}")

print(f"\n共创建 {len(CASES)} 个复现实例")
