# Source Generated with Decompyle++ (Python version)
# File: repro_05_closure.pyc (Python 3.11)

def outer(rules):
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*(args), **(kwargs))
        return wrapper
    return decorator
