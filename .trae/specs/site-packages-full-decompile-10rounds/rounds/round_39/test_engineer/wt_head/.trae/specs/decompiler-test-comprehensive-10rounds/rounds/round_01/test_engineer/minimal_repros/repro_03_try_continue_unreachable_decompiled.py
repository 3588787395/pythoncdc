# Source Generated with Decompyle++ (Python version)
# File: repro_03_try_continue_unreachable.pyc (Python 3.11)

__doc__ = '复现03: try-except-finally + for-continue结构中continue后代码被错误保留'
def process(data):
    result = {'count': 0}
    for item in data:
        try:
            converted = int(item)
            result['count'] += 1
        except Exception as e:
            result['errors'] = str(e)
        finally:
            pass
    else:
        return result
