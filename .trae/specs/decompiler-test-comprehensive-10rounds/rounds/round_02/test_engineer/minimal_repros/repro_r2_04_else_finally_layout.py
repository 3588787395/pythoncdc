"""复现R2-04: try-except-else-finally中else的return与finally的字节码布局差异"""
def test_else_finally_layout(data):
    results = {}
    try:
        results['val'] = data
    except Exception as e:
        results['err'] = str(e)
    else:
        return results
    finally:
        results['final'] = 'done'
