"""复现12: try-except-else-finally中finally块位置错误"""
def test_finally_position(data):
    results = {}
    try:
        if data:
            results['data'] = data
    except Exception as e:
        results['error'] = str(e)
    else:
        return results
    finally:
        results['final'] = 'completed'
