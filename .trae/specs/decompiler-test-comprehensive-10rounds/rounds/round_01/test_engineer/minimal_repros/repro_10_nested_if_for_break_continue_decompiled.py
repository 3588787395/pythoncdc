# Source Generated with Decompyle++ (Python version)
# File: repro_10_nested_if_for_break_continue.pyc (Python 3.11)

__doc__ = '复现10: 多层嵌套if-elif-else在for循环内的break/continue路径错误'
def test_nested_if_for(data):
    for i, item in enumerate(data):
        if isinstance(item, int):
            if item < 0:
                continue
            elif item > 100:
                break
        elif isinstance(item, str):
            if len(item) == 0:
                break
            elif not len(item) > 50:
                continue
            else:
                return False
        else:
            break
    return True
