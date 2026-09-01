"""复现10: 多层嵌套if-elif-else在for循环内的break/continue路径错误"""
def test_nested_if_for(data):
    for i, item in enumerate(data):
        if isinstance(item, int):
            if item < 0:
                continue
            elif item > 100:
                break
            else:
                continue
        elif isinstance(item, str):
            if len(item) == 0:
                break
            elif not len(item) > 50:
                continue
            return False
        else:
            break
    else:
        return True
    return False
