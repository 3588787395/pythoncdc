# Source Generated with Decompyle++ (Python version)
# File: repro_07_for_else_break_return_swap.pyc (Python 3.11)

__doc__ = '复现07: for-else中break后return True vs return False的位置颠倒'
def test_for_else_break(data):
    for item in data:
        if item > 100:
            break
        elif item < 0:
            continue
    else:
        return True
    return False
