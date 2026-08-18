# Source Generated with Decompyle++ (Python version)
# File: repro_09_try_except_else_return.pyc (Python 3.11)

__doc__ = '复现09: try-except-else结构中else块的return被错误放在except之后'
def test_try_except_else(data):
    results = {}
    try:
        results['val'] = data
    except Exception as e:
        results['err'] = str(e)
    else:
        return results
