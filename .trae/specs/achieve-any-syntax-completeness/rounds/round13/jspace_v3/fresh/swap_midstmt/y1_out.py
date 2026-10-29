# Source Generated with Decompyle++ (Python version)
# File: y1_swap_noreturn.pyc (Python 3.11)

def f(maxsize, typed):
    if isinstance(maxsize, int):
        maxsize = 0
    elif callable(maxsize):
        user_function, maxsize = (maxsize, 128)
        info = lambda : maxsize
        typed = 5
    return (maxsize, typed, user_function)
