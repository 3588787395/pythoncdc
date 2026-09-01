# Source Generated with Decompyle++ (Python version)
# File: repro_r2_06_nested_try_else.pyc (Python 3.11)

__doc__ = '复现R2-06: 嵌套try-except中内层try的else块识别'
def test_nested_try_else(data):
    result = []
    for item in data:
        try:
            converted = int(item)
            result.append(converted)
        except ValueError:
            result.append(0)
        else:
            try:
                print(f'done: {item}')
            except Exception as e:
                result.append(-1)
                continue
    else:
        return result
