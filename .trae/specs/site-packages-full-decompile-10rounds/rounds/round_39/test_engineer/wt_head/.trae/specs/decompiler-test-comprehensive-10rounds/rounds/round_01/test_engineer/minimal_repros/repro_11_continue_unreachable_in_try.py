"""复现11: continue后跟不可达代码在try块内"""
def test_continue_in_try(data):
    result = []
    for item in data:
        try:
            if item > 0:
                result.append(item)
                continue
                result.append(item)  # 不可达
        except Exception:
            pass
    return result
