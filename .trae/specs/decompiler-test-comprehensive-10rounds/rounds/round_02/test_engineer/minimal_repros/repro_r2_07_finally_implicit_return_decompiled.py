# Source Generated with Decompyle++ (Python version)
# File: repro_r2_07_finally_implicit_return.pyc (Python 3.11)

__doc__ = '复现R2-07: try-except-finally中finally后有隐式return None'
def test_finally_implicit_return(data):
    results = {}
    try:
        results['val'] = data
    except Exception as e:
        results['err'] = str(e)
    else:
        return results
    finally:
        results['final'] = 'done'
    return None
