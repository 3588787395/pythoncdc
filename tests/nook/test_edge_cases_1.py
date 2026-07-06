"""
边界情况测试 - 阶段2
测试各种边界情况和复杂组合
"""


# ========== 空循环体测试 ==========

def empty_while_loop():
    """空while循环体"""
    i = 0
    while i < 10:
        pass  # 空循环体
        i += 1
    return i


def empty_for_loop():
    """空for循环体"""
    for i in range(10):
        pass  # 空循环体
    return i


def empty_while_with_else():
    """空while循环体带else"""
    i = 0
    while i < 5:
        pass
        i += 1
    else:
        print("Loop completed")
    return i


def empty_for_with_else():
    """空for循环体带else"""
    for i in range(5):
        pass
    else:
        print("Loop completed")
    return i


# ========== 单条语句循环 ==========

def single_statement_while():
    """单条语句while循环"""
    i = 0
    while i < 10: i += 1
    return i


def single_statement_for():
    """单条语句for循环"""
    total = 0
    for i in range(10): total += i
    return total


def single_statement_if_in_while():
    """while内单条语句if"""
    i = 0
    while i < 10:
        if i % 2 == 0: print(i)
        i += 1
    return i


# ========== 复杂循环条件 ==========

def complex_while_condition_and():
    """复杂while条件 - and"""
    i = 0
    j = 0
    while i < 10 and j < 20:
        i += 1
        j += 2
    return i, j


def complex_while_condition_or():
    """复杂while条件 - or"""
    i = 0
    j = 0
    while i < 5 or j < 10:
        i += 1
        j += 1
    return i, j


def complex_while_condition_mixed():
    """复杂while条件 - 混合and/or"""
    i = 0
    j = 0
    k = 0
    while (i < 5 and j < 10) or k > 3:
        i += 1
        j += 2
        k -= 1
    return i, j, k


def complex_for_with_if_condition():
    """for循环内复杂if条件"""
    result = []
    for i in range(20):
        if i > 5 and i < 15 and i % 2 == 0:
            result.append(i)
    return result


# ========== 循环内多重if-elif-else ==========

def nested_if_elif_else_in_while():
    """while内多重if-elif-else"""
    i = 0
    result = []
    while i < 10:
        if i < 3:
            result.append("small")
        elif i < 6:
            result.append("medium")
        elif i < 9:
            result.append("large")
        else:
            result.append("extra_large")
        i += 1
    return result


def nested_if_elif_else_in_for():
    """for内多重if-elif-else"""
    result = []
    for i in range(10):
        if i % 3 == 0:
            result.append("divisible_by_3")
        elif i % 3 == 1:
            result.append("remainder_1")
        else:
            result.append("remainder_2")
    return result


def deeply_nested_if_in_loop():
    """深层嵌套if在循环内"""
    result = []
    for i in range(5):
        if i > 0:
            if i > 1:
                if i > 2:
                    result.append("deep")
                else:
                    result.append("medium")
            else:
                result.append("shallow")
        else:
            result.append("surface")
    return result


# ========== 边界值测试 ==========

def loop_with_zero_iterations():
    """零次迭代的循环"""
    count = 0
    for i in range(0):
        count += 1
    return count


def loop_with_single_iteration():
    """单次迭代的循环"""
    count = 0
    for i in range(1):
        count += 1
    return count


def infinite_loop_with_break():
    """带break的无限循环"""
    i = 0
    while True:
        if i >= 10:
            break
        i += 1
    return i


# ========== 复杂控制流组合 ==========

def loop_with_multiple_breaks():
    """多个break的循环"""
    result = []
    for i in range(20):
        if i == 5:
            break
        if i == 3:
            continue
        result.append(i)
    return result


def loop_with_multiple_continues():
    """多个continue的循环"""
    result = []
    for i in range(10):
        if i % 2 == 0:
            continue
        if i % 3 == 0:
            continue
        result.append(i)
    return result


def nested_loop_with_complex_control():
    """嵌套循环复杂控制流"""
    result = []
    for i in range(5):
        for j in range(5):
            if i == j:
                continue
            if i + j == 4:
                break
            result.append((i, j))
    return result


if __name__ == "__main__":
    # 运行所有测试函数
    test_functions = [
        empty_while_loop,
        empty_for_loop,
        empty_while_with_else,
        empty_for_with_else,
        single_statement_while,
        single_statement_for,
        single_statement_if_in_while,
        complex_while_condition_and,
        complex_while_condition_or,
        complex_while_condition_mixed,
        complex_for_with_if_condition,
        nested_if_elif_else_in_while,
        nested_if_elif_else_in_for,
        deeply_nested_if_in_loop,
        loop_with_zero_iterations,
        loop_with_single_iteration,
        infinite_loop_with_break,
        loop_with_multiple_breaks,
        loop_with_multiple_continues,
        nested_loop_with_complex_control,
    ]
    
    print("Running edge case tests...")
    for func in test_functions:
        try:
            result = func()
            print(f"✓ {func.__name__}: {result}")
        except Exception as e:
            print(f"✗ {func.__name__}: {e}")
