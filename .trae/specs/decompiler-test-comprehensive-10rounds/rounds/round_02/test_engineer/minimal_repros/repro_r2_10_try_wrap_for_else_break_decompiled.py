# Source Generated with Decompyle++ (Python version)
# File: repro_r2_10_try_wrap_for_else_break.pyc (Python 3.11)

__doc__ = '复现R2-10: try-except包裹for-else，break后return在循环外'
def test_try_wrap_for_else_break(data):
    try:
        for item in data:
            if isinstance(item, int):
                if item > 100:
                    break
                continue
            break
        else:
            return True
    except Exception as e:
        return False
