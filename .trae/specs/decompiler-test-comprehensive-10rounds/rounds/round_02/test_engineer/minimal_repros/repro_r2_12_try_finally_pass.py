"""复现R2-12: try-finally中finally pass的简化"""
def test_try_finally_pass(data):
    result = []
    for item in data:
        try:
            converted = int(item)
            result.append(converted)
            continue
        except Exception:
            pass
        finally:
            pass
    else:
        return result
