"""复现08: try-except包裹for-else结构，循环退出路径处理错误"""
def test_try_for_else(data):
    try:
        for item in data:
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
    except Exception as e:
        return False
