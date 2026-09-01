# Source Generated with Decompyle++ (Python version)
# File: repro_08_try_wrap_for_else.pyc (Python 3.11)

__doc__ = '复现08: try-except包裹for-else结构，循环退出路径处理错误'
def test_try_for_else(data):
    try:
        for item in data:
            if isinstance(item, int):
                if item < 0:
                    continue
            else:
                break
            if item < 0:
                continue
            elif item > 100:
                break
        else:
            return True
    except Exception as e:
        return False
        return False
