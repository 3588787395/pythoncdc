"""
海象运算符在推导式中的错误实例

问题: 列表推导式中的海象运算符有时无法正确识别
"""

# 列表推导式中的海象运算符
def test_listcomp_walrus():
    # 这个应该正常工作
    results = [(x := i * 2) for i in range(3)]
    return results

# 嵌套推导式
def test_nested_comprehension():
    # 复杂情况
    matrix = [[(val := i * j) for j in range(3)] for i in range(3)]
    return matrix
