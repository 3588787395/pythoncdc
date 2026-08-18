# Source Generated with Decompyle++ (Python version)
# File: repro_r2_02_continue_unreachable.pyc (Python 3.11)

__doc__ = '复现R2-02: continue后不可达代码被保留'
def test_continue_unreachable(data):
    result = {'count': 0}
    for item in data:
        try:
            if item > 0:
                result['count'] += 1
                continue
            continue
        except Exception:
            continue
    else:
        return result
