def f(items):
    try:
        while items:
            return items.pop()
    except BaseException:
        return None
