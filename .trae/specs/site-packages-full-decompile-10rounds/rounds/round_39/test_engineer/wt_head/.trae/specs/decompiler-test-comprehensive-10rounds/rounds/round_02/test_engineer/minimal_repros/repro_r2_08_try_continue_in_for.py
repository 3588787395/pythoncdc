"""复现R2-08: for循环中try-except-continue结构"""
def test_try_continue_in_for(data):
    result = []
    for item in data:
        try:
            if item > 0:
                result.append(item)
                continue
        except Exception:
            pass
    return result
