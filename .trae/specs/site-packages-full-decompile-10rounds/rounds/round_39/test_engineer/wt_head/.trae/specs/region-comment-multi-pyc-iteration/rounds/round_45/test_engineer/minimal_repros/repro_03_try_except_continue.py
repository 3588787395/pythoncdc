
def func(items):
    for item in items:
        try:
            if item > 0:
                continue
            return item
        except Exception:
            continue
    return None
