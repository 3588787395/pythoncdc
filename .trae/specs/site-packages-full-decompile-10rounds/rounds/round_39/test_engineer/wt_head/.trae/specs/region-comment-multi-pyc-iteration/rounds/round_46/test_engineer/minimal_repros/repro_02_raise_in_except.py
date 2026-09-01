def func(x):
    try:
        return x + 1
    except ValueError:
        raise ValueError("re-raise")
