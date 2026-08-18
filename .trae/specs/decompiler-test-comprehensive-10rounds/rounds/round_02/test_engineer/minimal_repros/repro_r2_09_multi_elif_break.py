"""复现R2-09: 多层if-elif-else中break后的代码路径"""
def test_multi_elif_break(data):
    for i, item in enumerate(data):
        if isinstance(item, int):
            if item < 0:
                continue
            elif item > 100:
                break
            else:
                continue
        else:
            break
    else:
        return True
    return False
