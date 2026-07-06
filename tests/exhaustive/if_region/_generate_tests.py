import os

base_dir = r'd:\Desktop\ptrade相关\pythoncdc\tests\exhaustive\if_region'

tests = [
    (39, 'ifelifassign', [
        ('a', 'a', 'if a > 0:\n    a = 1\nelif a < 0:\n    a = -1'),
        ('n', 'n', 'if n > 0:\n    n = 1\nelif n < 0:\n    n = -1'),
        ('x', 'x', 'if x > 0:\n    x = 1\nelif x < 0:\n    x = -1'),
    ]),
    (40, 'ifelifelsereturn', [
        ('a', 'a', 'def f(a):\n    if a > 0:\n        return 1\n    elif a < 0:\n        return -1\n    else:\n        return 0'),
        ('n', 'n', 'def f(n):\n    if n > 0:\n        return 1\n    elif n < 0:\n        return -1\n    else:\n        return 0'),
        ('x', 'x', 'def f(x):\n    if x > 0:\n        return 1\n    elif x < 0:\n        return -1\n    else:\n        return 0'),
    ]),
    (41, 'ifelifnestedif', [
        ('a', 'a', 'if a > 0:\n    a = 1\nelif a < 0:\n    if a < -10:\n        a = -10'),
        ('n', 'n', 'if n > 0:\n    n = 1\nelif n < 0:\n    if n < -10:\n        n = -10'),
        ('x', 'x', 'if x > 0:\n    x = 1\nelif x < 0:\n    if x < -10:\n        x = -10'),
    ]),
    (42, 'ifinfor', [
        ('a', 'a', 'for i in range(10):\n    if a > i:\n        a = i'),
        ('n', 'n', 'for i in range(10):\n    if n > i:\n        n = i'),
        ('x', 'x', 'for i in range(10):\n    if x > i:\n        x = i'),
    ]),
    (43, 'ifinwhile', [
        ('a', 'a', 'while a > 0:\n    if a > 5:\n        a = a - 5\n    else:\n        a = a - 1'),
        ('n', 'n', 'while n > 0:\n    if n > 5:\n        n = n - 5\n    else:\n        n = n - 1'),
        ('x', 'x', 'while x > 0:\n    if x > 5:\n        x = x - 5\n    else:\n        x = x - 1'),
    ]),
    (44, 'ifintry', [
        ('a', 'a', 'try:\n    if a > 0:\n        a = 1\nexcept:\n    a = 0'),
        ('n', 'n', 'try:\n    if n > 0:\n        n = 1\nexcept:\n    n = 0'),
        ('x', 'x', 'try:\n    if x > 0:\n        x = 1\nexcept:\n    x = 0'),
    ]),
    (45, 'ifinwith', [
        ('a', 'a', 'with open("f") as f:\n    if a > 0:\n        a = 1'),
        ('n', 'n', 'with open("f") as f:\n    if n > 0:\n        n = 1'),
        ('x', 'x', 'with open("f") as f:\n    if x > 0:\n        x = 1'),
    ]),
    (46, 'ifinifelse', [
        ('a_b', 'a_b', 'if a > 0:\n    a = 1\nelse:\n    if a < -5:\n        a = -5'),
        ('n_m', 'n_m', 'if n > 0:\n    n = 1\nelse:\n    if n < -5:\n        n = -5'),
        ('x_y', 'x_y', 'if x > 0:\n    x = 1\nelse:\n    if x < -5:\n        x = -5'),
    ]),
    (47, 'ifandor', [
        ('a_b', 'a_b', 'if a > 0 and b > 0 or c > 0:\n    pass'),
        ('n_m', 'n_m', 'if n > 0 and m > 0 or k > 0:\n    pass'),
        ('x_y', 'x_y', 'if x > 0 and y > 0 or z > 0:\n    pass'),
    ]),
    (48, 'ifchainedand', [
        ('a_b', 'a_b', 'if a > 0 and b > 0 and c > 0:\n    pass'),
        ('n_m', 'n_m', 'if n > 0 and m > 0 and k > 0:\n    pass'),
        ('x_y', 'x_y', 'if x > 0 and y > 0 and z > 0:\n    pass'),
    ]),
    (49, 'ifchainedor', [
        ('a_b', 'a_b', 'if a > 0 or b > 0 or c > 0:\n    pass'),
        ('n_m', 'n_m', 'if n > 0 or m > 0 or k > 0:\n    pass'),
        ('x_y', 'x_y', 'if x > 0 or y > 0 or z > 0:\n    pass'),
    ]),
    (50, 'ifnotand', [
        ('a_b', 'a_b', 'if not (a and b):\n    pass'),
        ('n_m', 'n_m', 'if not (n and m):\n    pass'),
        ('x_y', 'x_y', 'if not (x and y):\n    pass'),
    ]),
    (51, 'ifnotor', [
        ('a_b', 'a_b', 'if not (a or b):\n    pass'),
        ('n_m', 'n_m', 'if not (n or m):\n    pass'),
        ('x_y', 'x_y', 'if not (x or y):\n    pass'),
    ]),
    (52, 'ifintuple', [
        ('a', 'a', 'if a in (1, 2, 3):\n    pass'),
        ('n', 'n', 'if n in (1, 2, 3):\n    pass'),
        ('x', 'x', 'if x in (1, 2, 3):\n    pass'),
    ]),
    (53, 'ifisbool', [
        ('a', 'a', 'if a is True:\n    pass'),
        ('n', 'n', 'if n is False:\n    pass'),
        ('x', 'x', 'if x is True:\n    pass'),
    ]),
    (54, 'ifyield', [
        ('a', 'a', 'def f(a):\n    if a > 0:\n        yield a'),
        ('n', 'n', 'def f(n):\n    if n > 0:\n        yield n'),
        ('x', 'x', 'def f(x):\n    if x > 0:\n        yield x'),
    ]),
    (55, 'ifdel', [
        ('a', 'a', 'd = {"a": 1}\nif a > 0:\n    del d["a"]'),
        ('n', 'n', 'd = {"n": 1}\nif n > 0:\n    del d["n"]'),
        ('x', 'x', 'd = {"x": 1}\nif x > 0:\n    del d["x"]'),
    ]),
    (56, 'ifemptyelse', [
        ('a', 'a', 'if a > 0:\n    a = 1\nelse:\n    pass'),
        ('n', 'n', 'if n > 0:\n    n = 1\nelse:\n    pass'),
        ('x', 'x', 'if x > 0:\n    x = 1\nelse:\n    pass'),
    ]),
    (57, 'ifassert', [
        ('a', 'a', 'if a > 0:\n    assert a > 0'),
        ('n', 'n', 'if n > 0:\n    assert n > 0'),
        ('x', 'x', 'if x > 0:\n    assert x > 0'),
    ]),
    (58, 'ifaugassign', [
        ('a', 'a', 'if a > 0:\n    a += 1'),
        ('n', 'n', 'if n > 0:\n    n += 1'),
        ('x', 'x', 'if x > 0:\n    x += 1'),
    ]),
    (59, 'ifelifreturn', [
        ('a', 'a', 'def f(a):\n    if a > 0:\n        a = 1\n    elif a < 0:\n        return -1\n    return 0'),
        ('n', 'n', 'def f(n):\n    if n > 0:\n        n = 1\n    elif n < 0:\n        return -1\n    return 0'),
        ('x', 'x', 'def f(x):\n    if x > 0:\n        x = 1\n    elif x < 0:\n        return -1\n    return 0'),
    ]),
    (60, 'ifelsebreak', [
        ('a', 'a', 'for i in range(10):\n    if a > i:\n        a = i\n    else:\n        break'),
        ('n', 'n', 'for i in range(10):\n    if n > i:\n        n = i\n    else:\n        break'),
        ('x', 'x', 'for i in range(10):\n    if x > i:\n        x = i\n    else:\n        break'),
    ]),
    (61, 'ifelsecontinue', [
        ('a', 'a', 'for i in range(10):\n    if a > i:\n        a = i\n    else:\n        continue'),
        ('n', 'n', 'for i in range(10):\n    if n > i:\n        n = i\n    else:\n        continue'),
        ('x', 'x', 'for i in range(10):\n    if x > i:\n        x = i\n    else:\n        continue'),
    ]),
    (62, 'ifelseraise', [
        ('a_IndexError', 'a_IndexError', 'if a > 0:\n    a = 1\nelse:\n    raise IndexError'),
        ('n_StopIteration', 'n_StopIteration', 'if n > 0:\n    n = 1\nelse:\n    raise StopIteration'),
        ('x_ValueError', 'x_ValueError', 'if x > 0:\n    x = 1\nelse:\n    raise ValueError'),
    ]),
    (63, 'ifmultireturn', [
        ('a', 'a', 'def f(a):\n    if a > 0:\n        return 1\n    elif a == 0:\n        return 0\n    else:\n        return -1'),
        ('n', 'n', 'def f(n):\n    if n > 0:\n        return 1\n    elif n == 0:\n        return 0\n    else:\n        return -1'),
        ('x', 'x', 'def f(x):\n    if x > 0:\n        return 1\n    elif x == 0:\n        return 0\n    else:\n        return -1'),
    ]),
    (64, 'ifstringcompare', [
        ('a', 'a', 'if a == "hello":\n    a = "world"'),
        ('n', 'n', 'if n == "hello":\n    n = "world"'),
        ('x', 'x', 'if x == "hello":\n    x = "world"'),
    ]),
    (65, 'ifboolopcompare', [
        ('a_b', 'a_b', 'if a > 0 and b < 10:\n    pass'),
        ('n_m', 'n_m', 'if n > 0 and m < 10:\n    pass'),
        ('x_y', 'x_y', 'if x > 0 and y < 10:\n    pass'),
    ]),
    (66, 'ifisnoneelse', [
        ('a', 'a', 'if a is None:\n    a = 0\nelse:\n    a = a + 1'),
        ('n', 'n', 'if n is None:\n    n = 0\nelse:\n    n = n + 1'),
        ('x', 'x', 'if x is None:\n    x = 0\nelse:\n    x = x + 1'),
    ]),
    (67, 'ifdoublenested', [
        ('a', 'a', 'if a > 0:\n    if a > 10:\n        if a > 100:\n            a = 100'),
        ('n', 'n', 'if n > 0:\n    if n > 10:\n        if n > 100:\n            n = 100'),
        ('x', 'x', 'if x > 0:\n    if x > 10:\n        if x > 100:\n            x = 100'),
    ]),
    (68, 'ifelifinfor', [
        ('a', 'a', 'for i in range(10):\n    if a > i:\n        a = i\n    elif a == i:\n        a = 0'),
        ('n', 'n', 'for i in range(10):\n    if n > i:\n        n = i\n    elif n == i:\n        n = 0'),
        ('x', 'x', 'for i in range(10):\n    if x > i:\n        x = i\n    elif x == i:\n        x = 0'),
    ]),
    (69, 'ifnonlocal', [
        ('a', 'a', 'def f():\n    a = 1\n    def g():\n        nonlocal a\n        if a > 0:\n            a = 2'),
        ('n', 'n', 'def f():\n    n = 1\n    def g():\n        nonlocal n\n        if n > 0:\n            n = 2'),
        ('x', 'x', 'def f():\n    x = 1\n    def g():\n        nonlocal x\n        if x > 0:\n            x = 2'),
    ]),
    (70, 'ifglobal', [
        ('a', 'a', 'def f():\n    global a\n    if a > 0:\n        a = 2'),
        ('n', 'n', 'def f():\n    global n\n    if n > 0:\n        n = 2'),
        ('x', 'x', 'def f():\n    global x\n    if x > 0:\n        x = 2'),
    ]),
    (71, 'ifyieldfrom', [
        ('a', 'a', 'def f(a):\n    if a > 0:\n        yield from range(a)'),
        ('n', 'n', 'def f(n):\n    if n > 0:\n        yield from range(n)'),
        ('x', 'x', 'def f(x):\n    if x > 0:\n        yield from range(x)'),
    ]),
    (72, 'ifternarybody', [
        ('a', 'a', 'if a > 0:\n    b = 1 if a > 10 else 2'),
        ('n', 'n', 'if n > 0:\n    m = 1 if n > 10 else 2'),
        ('x', 'x', 'if x > 0:\n    y = 1 if x > 10 else 2'),
    ]),
    (73, 'ifelifelseassign', [
        ('a', 'a', 'if a > 0:\n    a = 1\nelif a == 0:\n    a = 0\nelse:\n    a = -1'),
        ('n', 'n', 'if n > 0:\n    n = 1\nelif n == 0:\n    n = 0\nelse:\n    n = -1'),
        ('x', 'x', 'if x > 0:\n    x = 1\nelif x == 0:\n    x = 0\nelse:\n    x = -1'),
    ]),
    (74, 'ifindictcompare', [
        ('a', 'a', 'd = {1: 2}\nif a in d:\n    a = d[a]'),
        ('n', 'n', 'd = {1: 2}\nif n in d:\n    n = d[n]'),
        ('x', 'x', 'd = {1: 2}\nif x in d:\n    x = d[x]'),
    ]),
    (75, 'ifmultielifreturn', [
        ('a', 'a', 'def f(a):\n    if a == 1:\n        return 1\n    elif a == 2:\n        return 2\n    elif a == 3:\n        return 3\n    return 0'),
        ('n', 'n', 'def f(n):\n    if n == 1:\n        return 1\n    elif n == 2:\n        return 2\n    elif n == 3:\n        return 3\n    return 0'),
        ('x', 'x', 'def f(x):\n    if x == 1:\n        return 1\n    elif x == 2:\n        return 2\n    elif x == 3:\n        return 3\n    return 0'),
    ]),
    (76, 'ifnestedelseif', [
        ('a', 'a', 'if a > 0:\n    a = 1\nelse:\n    if a < -10:\n        a = -10\n    else:\n        a = 0'),
        ('n', 'n', 'if n > 0:\n    n = 1\nelse:\n    if n < -10:\n        n = -10\n    else:\n        n = 0'),
        ('x', 'x', 'if x > 0:\n    x = 1\nelse:\n    if x < -10:\n        x = -10\n    else:\n        x = 0'),
    ]),
    (77, 'ifelifelsemultistmt', [
        ('a', 'a', 'if a > 0:\n    a = 1\n    b = 2\nelif a < 0:\n    a = -1\n    b = -2\nelse:\n    a = 0\n    b = 0'),
        ('n', 'n', 'if n > 0:\n    n = 1\n    m = 2\nelif n < 0:\n    n = -1\n    m = -2\nelse:\n    n = 0\n    m = 0'),
        ('x', 'x', 'if x > 0:\n    x = 1\n    y = 2\nelif x < 0:\n    x = -1\n    y = -2\nelse:\n    x = 0\n    y = 0'),
    ]),
    (78, 'ifinlistcomp', [
        ('a', 'a', 'r = [i for i in range(10) if a > i]'),
        ('n', 'n', 'r = [i for i in range(10) if n > i]'),
        ('x', 'x', 'r = [i for i in range(10) if x > i]'),
    ]),
    (79, 'ifelseaugassign', [
        ('a', 'a', 'if a > 0:\n    a += 1\nelse:\n    a -= 1'),
        ('n', 'n', 'if n > 0:\n    n += 1\nelse:\n    n -= 1'),
        ('x', 'x', 'if x > 0:\n    x += 1\nelse:\n    x -= 1'),
    ]),
    (80, 'ifelifbreak', [
        ('a', 'a', 'for i in range(10):\n    if a > i:\n        a = i\n    elif a == 5:\n        break'),
        ('n', 'n', 'for i in range(10):\n    if n > i:\n        n = i\n    elif n == 5:\n        break'),
        ('x', 'x', 'for i in range(10):\n    if x > i:\n        x = i\n    elif x == 5:\n        break'),
    ]),
    (81, 'ifelifcontinue', [
        ('a', 'a', 'for i in range(10):\n    if a > i:\n        a = i\n    elif a == 5:\n        continue'),
        ('n', 'n', 'for i in range(10):\n    if n > i:\n        n = i\n    elif n == 5:\n        continue'),
        ('x', 'x', 'for i in range(10):\n    if x > i:\n        x = i\n    elif x == 5:\n        continue'),
    ]),
    (82, 'ifnotindict', [
        ('a', 'a', 'd = {1: 2}\nif a not in d:\n    d[a] = 0'),
        ('n', 'n', 'd = {1: 2}\nif n not in d:\n    d[n] = 0'),
        ('x', 'x', 'd = {1: 2}\nif x not in d:\n    d[x] = 0'),
    ]),
    (83, 'ifelsedel', [
        ('a', 'a', 'd = {"k": 1}\nif a > 0:\n    d["k"] = a\nelse:\n    del d["k"]'),
        ('n', 'n', 'd = {"k": 1}\nif n > 0:\n    d["k"] = n\nelse:\n    del d["k"]'),
        ('x', 'x', 'd = {"k": 1}\nif x > 0:\n    d["k"] = x\nelse:\n    del d["k"]'),
    ]),
    (84, 'ifchainedcompareelse', [
        ('a', 'a', 'if 0 < a < 10:\n    a = a + 1\nelse:\n    a = 0'),
        ('n', 'n', 'if 0 < n < 10:\n    n = n + 1\nelse:\n    n = 0'),
        ('x', 'x', 'if 0 < x < 10:\n    x = x + 1\nelse:\n    x = 0'),
    ]),
    (85, 'ifelseyield', [
        ('a', 'a', 'def f(a):\n    if a > 0:\n        yield a\n    else:\n        yield 0'),
        ('n', 'n', 'def f(n):\n    if n > 0:\n        yield n\n    else:\n        yield 0'),
        ('x', 'x', 'def f(x):\n    if x > 0:\n        yield x\n    else:\n        yield 0'),
    ]),
    (86, 'ifnestedfor', [
        ('a', 'a', 'if a > 0:\n    for i in range(a):\n        a = a - 1'),
        ('n', 'n', 'if n > 0:\n    for i in range(n):\n        n = n - 1'),
        ('x', 'x', 'if x > 0:\n    for i in range(x):\n        x = x - 1'),
    ]),
    (87, 'ifnestedwhile', [
        ('a', 'a', 'if a > 0:\n    while a > 10:\n        a = a - 1'),
        ('n', 'n', 'if n > 0:\n    while n > 10:\n        n = n - 1'),
        ('x', 'x', 'if x > 0:\n    while x > 10:\n        x = x - 1'),
    ]),
    (88, 'ifnestedtry', [
        ('a', 'a', 'if a > 0:\n    try:\n        a = int(a)\n    except:\n        a = 0'),
        ('n', 'n', 'if n > 0:\n    try:\n        n = int(n)\n    except:\n        n = 0'),
        ('x', 'x', 'if x > 0:\n    try:\n        x = int(x)\n    except:\n        x = 0'),
    ]),
    (89, 'ifnestedwith', [
        ('a', 'a', 'if a > 0:\n    with open("f") as f:\n        a = f.read()'),
        ('n', 'n', 'if n > 0:\n    with open("f") as f:\n        n = f.read()'),
        ('x', 'x', 'if x > 0:\n    with open("f") as f:\n        x = f.read()'),
    ]),
    (90, 'ifelifelseraise', [
        ('a_IndexError', 'a_IndexError', 'if a > 0:\n    pass\nelif a == 0:\n    raise IndexError\nelse:\n    raise ValueError'),
        ('n_StopIteration', 'n_StopIteration', 'if n > 0:\n    pass\nelif n == 0:\n    raise StopIteration\nelse:\n    raise TypeError'),
        ('x_RuntimeError', 'x_RuntimeError', 'if x > 0:\n    pass\nelif x == 0:\n    raise RuntimeError\nelse:\n    raise KeyError'),
    ]),
]

count = 0
for test_id, name, variants in tests:
    for suffix, class_suffix, source_code in variants:
        filename = f'test_if{test_id:02d}{name}_{suffix}.py'
        filepath = os.path.join(base_dir, filename)

        class_name = f'TestIF{test_id:02d}{name[0].upper()}{name[1:]}_{class_suffix}'

        content = f'''import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class {class_name}(ExhaustiveTestCase):
    SOURCE_CODE = """{source_code}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
'''

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        count += 1

print(f'Created {count} test files')
