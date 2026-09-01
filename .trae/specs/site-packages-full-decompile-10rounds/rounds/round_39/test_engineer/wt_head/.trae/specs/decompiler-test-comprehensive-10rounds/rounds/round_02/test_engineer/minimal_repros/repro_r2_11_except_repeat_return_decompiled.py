# Source Generated with Decompyle++ (Python version)
# File: repro_r2_11_except_repeat_return.pyc (Python 3.11)

__doc__ = '复现R2-11: except handler中重复return'
def test_except_repeat_return(data):
    try:
        for item in data:
            if item > 100:
                break
            continue
        else:
            return True
    except Exception as e:
        print(f'error: {e}')
        return False
    return False
