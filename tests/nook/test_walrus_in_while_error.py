"""
while循环中的海象运算符错误实例

问题: while循环中的海象运算符有时无法正确识别条件
"""

def test_while_walrus():
    count = 0
    # while循环中的海象运算符
    while (data := count * 2) < 10:
        count += 1
    return count

def test_while_complex_condition():
    # 复杂条件
    total = 0
    i = 0
    while (val := i * 3) < 20 and i < 10:
        total += val
        i += 1
    return total
