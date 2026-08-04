# Source Generated with Decompyle++ (Python version)
# File: repro_11_nested_guard_clauses.cpython-311.pyc (Python 3.11)

__doc__ = """R27 repro_11: Nested if-raise (guard clauses)
   def f(x, y):
       if x is None:
           raise ValueError("x is None")
       if y is None:
           raise ValueError("y is None")
       if x > y:
           return x
       return y
"""
def f(x, y):
    if x is None:
        raise ValueError('x is None')
    elif y is None:
        raise ValueError('y is None')
    elif x > y:
        return x
    else:
        return y
