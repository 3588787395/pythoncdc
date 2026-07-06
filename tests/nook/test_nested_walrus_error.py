"""
嵌套海象运算符反编译错误实例

问题: 嵌套海象运算符 (a := (b := 5) + 1) 反编译后丢失内层海象运算符
期望: if (a := (b := 5) + 1) > 5:
实际: if (a := 1) > 5:
"""

# 测试嵌套海象运算符
def test_nested_walrus():
    if (a := (b := 5) + 1) > 5:
        return a, b
    return None

# 另一个测试
def test_complex_nested():
    result = (x := (y := 10) * 2) + (z := 3)
    return result, x, y, z
