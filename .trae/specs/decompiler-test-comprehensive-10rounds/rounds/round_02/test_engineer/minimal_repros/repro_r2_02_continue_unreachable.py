"""复现R2-02: continue后不可达代码被保留"""
def test_continue_unreachable(data):
    result = {'count': 0}
    for item in data:
        try:
            if item > 0:
                result['count'] += 1
                continue
                result['count'] += 1
        except Exception:
            pass
    else:
        return result
