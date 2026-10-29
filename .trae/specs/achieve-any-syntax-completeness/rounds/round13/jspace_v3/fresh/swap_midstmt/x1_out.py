# Source Generated with Decompyle++ (Python version)
# File: x1_tuple_lambda_return.pyc (Python 3.11)

def g(*a):
    return None
def h(*a):
    return None
def f(maxsize, typed):
    if isinstance(maxsize, int):
        maxsize = 0
    elif callable(maxsize):
        user_function, maxsize = (maxsize, 128)
        info = lambda : maxsize
        return h(user_function)
    return (maxsize, typed)
