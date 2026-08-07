def func(x):
    if x < 0:
        raise ValueError("negative")
    elif x > 100:
        raise OverflowError("too large")
    return x
