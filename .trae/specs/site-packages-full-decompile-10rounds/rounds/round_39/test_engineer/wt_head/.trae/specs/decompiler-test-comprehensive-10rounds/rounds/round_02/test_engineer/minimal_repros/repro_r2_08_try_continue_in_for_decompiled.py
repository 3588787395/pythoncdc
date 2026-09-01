# Source Generated with Decompyle++ (Python version)
# File: repro_r2_08_try_continue_in_for.pyc (Python 3.11)

__doc__ = '复现R2-08: for循环中try-except-continue结构'
def test_try_continue_in_for(data):
    result = []
    for item in data:
        try:
            if item > 0:
                result.append(item)
                continue
            continue
        except Exception:
            continue
    else:
        return result
