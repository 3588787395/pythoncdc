"""复现R2-10: try-except包裹for-else，break后return在循环外"""
def test_try_wrap_for_else_break(data):
    try:
        for item in data:
            if isinstance(item, int):
                if item > 100:
                    break
                else:
                    continue
            else:
                break
        else:
            return True
        return False
    except Exception as e:
        return False
