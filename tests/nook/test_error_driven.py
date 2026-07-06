"""
错误驱动测试 - 阶段4
创建使反编译出错的实例，针对性修复
"""

import sys


# ========== 控制流识别错误测试 ==========

def complex_nested_loops_with_breaks():
    """复杂嵌套循环带多个break"""
    result = []
    for i in range(10):
        for j in range(10):
            for k in range(10):
                if i + j + k == 15:
                    result.append((i, j, k))
                    break
            else:
                continue
            break
        else:
            continue
        break
    return result


def loop_with_early_return():
    """循环内早期返回"""
    for i in range(100):
        if i == 50:
            return i
    return -1


def loop_with_multiple_returns():
    """循环内多个返回点"""
    for i in range(100):
        if i == 25:
            return i
        if i == 50:
            return i * 2
        if i == 75:
            return i * 3
    return -1


def deeply_nested_with_mixed_control():
    """深层嵌套混合控制流"""
    result = []
    for i in range(5):
        if i % 2 == 0:
            for j in range(3):
                while j < i:
                    if i + j == 3:
                        result.append((i, j))
                        break
                    j += 1
                else:
                    result.append((i, -1))
        else:
            if i > 2:
                continue
            result.append((i, None))
    return result


# ========== 条件表达式重建错误测试 ==========

def complex_boolean_expressions():
    """复杂布尔表达式"""
    result = []
    for i in range(20):
        if (i > 5 and i < 15) or (i % 2 == 0 and i % 3 != 0) or (i == 19):
            result.append(i)
    return result


def chained_comparisons():
    """链式比较"""
    result = []
    for i in range(10):
        if 2 < i < 5 < 7:
            result.append(i)
    return result


def complex_conditional_assignment():
    """复杂条件赋值"""
    result = []
    for i in range(10):
        x = i * 2 if i % 2 == 0 else i * 3 if i % 3 == 0 else i
        result.append(x)
    return result


def walrus_operator_in_loops():
    """循环内海象运算符"""
    result = []
    i = 0
    while (n := len(result)) < 10:
        result.append(n * i)
        i += 1
    return result


# ========== 循环边界识别错误测试 ==========

def loop_with_unusual_iterators():
    """不寻常迭代器"""
    result = []
    for i in iter(range(10)):
        result.append(i)
    for c in iter("hello"):
        result.append(c)
    return result


def loop_with_generator_expression():
    """生成器表达式循环"""
    result = []
    for x in (i * 2 for i in range(10)):
        result.append(x)
    return result


def loop_with_list_comprehension_result():
    """列表推导式结果循环"""
    result = []
    for x in [i ** 2 for i in range(10) if i % 2 == 0]:
        result.append(x)
    return result


def enumerate_with_start():
    """带起始索引的enumerate"""
    result = []
    for i, val in enumerate(['a', 'b', 'c'], start=1):
        result.append((i, val))
    return result


# ========== 嵌套结构处理错误测试 ==========

def nested_try_except_in_loop():
    """循环内嵌套try-except"""
    result = []
    for i in range(10):
        try:
            if i == 5:
                raise ValueError("test")
            result.append(i)
        except ValueError:
            result.append(-i)
        finally:
            result.append(i * 10)
    return result


def nested_with_in_loop():
    """循环内嵌套with语句"""
    result = []
    for i in range(5):
        with open(__file__, 'r') as f:
            lines = f.readlines()
            result.append(len(lines))
    return result


def loop_in_finally():
    """finally块中的循环"""
    result = []
    try:
        raise ValueError("test")
    except:
        result.append("caught")
    finally:
        for i in range(3):
            result.append(i)
    return result


def async_for_simulation():
    """异步for模拟（普通函数）"""
    result = []
    async_gen = [(i, i*2) for i in range(5)]
    for item in async_gen:
        result.append(item)
    return result


# ========== 代码生成格式错误测试 ==========

def loop_with_docstrings():
    """循环内文档字符串"""
    result = []
    for i in range(3):
        """This is a docstring inside a loop"""
        result.append(i)
    return result


def loop_with_comments_only():
    """只有注释的循环"""
    result = []
    for i in range(3):
        # This is just a comment
        # Another comment
        result.append(i)
    return result


def loop_with_multiline_strings():
    """多行字符串在循环中"""
    result = []
    for i in range(3):
        s = """
        Multiline
        string
        """
        result.append(s.strip())
    return result


def loop_with_fstring_formatting():
    """复杂f-string格式化"""
    result = []
    for i in range(5):
        s = f"Value: {i:03d}, Square: {i**2:5d}, Hex: {i:#x}"
        result.append(s)
    return result


# ========== 极端边界测试 ==========

def extremely_deep_nesting():
    """极端深层嵌套"""
    result = 0
    for a in range(2):
        for b in range(2):
            for c in range(2):
                for d in range(2):
                    for e in range(2):
                        result += a + b + c + d + e
    return result


def many_elif_in_loop():
    """循环内大量elif"""
    result = []
    for i in range(20):
        if i == 0:
            result.append("zero")
        elif i == 1:
            result.append("one")
        elif i == 2:
            result.append("two")
        elif i == 3:
            result.append("three")
        elif i == 4:
            result.append("four")
        elif i == 5:
            result.append("five")
        elif i == 6:
            result.append("six")
        elif i == 7:
            result.append("seven")
        elif i == 8:
            result.append("eight")
        elif i == 9:
            result.append("nine")
        else:
            result.append("other")
    return result


def loop_with_large_data():
    """处理大数据的循环"""
    data = list(range(1000))
    result = []
    for i, val in enumerate(data):
        if i % 100 == 0:
            result.append(val)
    return result


def mutually_recursive_loops():
    """模拟相互递归的循环"""
    result = []
    i = 0
    while i < 10:
        j = 0
        while j < i:
            result.append((i, j))
            j += 1
        i += 1
    return result


if __name__ == "__main__":
    test_functions = [
        complex_nested_loops_with_breaks,
        loop_with_early_return,
        loop_with_multiple_returns,
        deeply_nested_with_mixed_control,
        complex_boolean_expressions,
        chained_comparisons,
        complex_conditional_assignment,
        walrus_operator_in_loops,
        loop_with_unusual_iterators,
        loop_with_generator_expression,
        loop_with_list_comprehension_result,
        enumerate_with_start,
        nested_try_except_in_loop,
        nested_with_in_loop,
        loop_in_finally,
        async_for_simulation,
        loop_with_docstrings,
        loop_with_comments_only,
        loop_with_multiline_strings,
        loop_with_fstring_formatting,
        extremely_deep_nesting,
        many_elif_in_loop,
        loop_with_large_data,
        mutually_recursive_loops,
    ]
    
    print("Running error-driven tests...")
    passed = 0
    failed = 0
    for func in test_functions:
        try:
            result = func()
            print(f"✓ {func.__name__}: {str(result)[:50]}...")
            passed += 1
        except Exception as e:
            print(f"✗ {func.__name__}: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*60}")
