# Source Generated with Decompyle++ (Python version)
# File: repro_05_try_else_finally_return.pyc (Python 3.11)

__doc__ = '复现05: try-except-else-finally结构中else块的return位置错误'
def integration_test(data):
    results = {}
    try:
        if isinstance(data, list):
            results['data'] = data
    except Exception as e:
        results['error'] = str(e)
    else:
        return results
    finally:
        results['final'] = 'done'
