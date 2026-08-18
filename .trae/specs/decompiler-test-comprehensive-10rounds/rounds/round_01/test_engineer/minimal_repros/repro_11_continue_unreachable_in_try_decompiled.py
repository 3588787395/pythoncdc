# Source Generated with Decompyle++ (Python version)
# File: repro_11_continue_unreachable_in_try.pyc (Python 3.11)

__doc__ = '复现11: continue后跟不可达代码在try块内'
def test_continue_in_try(data):
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
