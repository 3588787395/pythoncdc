"""测试嵌套if-else结构"""

def test_nested_if_else(x, y):
    """嵌套if-else结构"""
    if x > 0:
        if y > 0:
            return 1
        else:
            return 2
    else:
        return 3
