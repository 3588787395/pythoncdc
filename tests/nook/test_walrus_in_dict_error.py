"""
字典中的海象运算符错误实例

问题: 字典值中的海象运算符有时无法正确识别
"""

def test_dict_walrus():
    # 字典中的海象运算符
    data = {
        'key1': (value1 := 1),
        'key2': (value2 := 2)
    }
    return data

def test_dict_complex_values():
    # 复杂表达式
    result = {
        'a': (x := 5 + 3),
        'b': (y := x * 2),
        'c': (z := y - 1)
    }
    return result
