
def func(x):
    try:
        result = x + 1
        return result
    except ValueError:
        return -1
    finally:
        cleanup = True
