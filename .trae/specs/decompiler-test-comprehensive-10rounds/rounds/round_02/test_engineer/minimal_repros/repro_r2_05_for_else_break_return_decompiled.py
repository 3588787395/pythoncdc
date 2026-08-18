# Source Generated with Decompyle++ (Python version)
# File: repro_r2_05_for_else_break_return.pyc (Python 3.11)

__doc__ = '复现R2-05: for-else中break后return False被放在for循环外'
def test_for_else_break_return(data):
    for item in data:
        if item > 100:
            break
        elif item < 0:
            continue
    else:
        return True
    return False
