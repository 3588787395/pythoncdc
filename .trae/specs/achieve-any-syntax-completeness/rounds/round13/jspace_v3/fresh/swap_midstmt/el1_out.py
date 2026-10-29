# Source Generated with Decompyle++ (Python version)
# File: el1_full.pyc (Python 3.11)

def g(*a):
    return None
def h(*a):
    return None
def f(maxsize, typed):
    if isinstance(maxsize, int):
        if maxsize < 0:
            maxsize = 0
    elif callable(maxsize) and isinstance(typed, bool):
        user_function, maxsize = (maxsize, 128)
        wrapper = g(user_function, maxsize, typed)
        wrapper.cache_parameters = lambda : {'maxsize': maxsize, 'typed': typed}
        return h(wrapper, user_function)
    elif maxsize is not None:
        raise TypeError('Expected first argument to be an integer, a callable, or None')
    return (maxsize, typed)
