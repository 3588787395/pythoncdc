# Source Generated with Decompyle++ (Python version)
# File: repro_r2_12_try_finally_pass.pyc (Python 3.11)

__doc__ = '复现R2-12: try-finally中finally pass的简化'
def test_try_finally_pass(data):
    result = []
    for item in data:
        try:
            converted = int(item)
            result.append(converted)
        except Exception:
            pass
        finally:
            pass
    else:
        return result
