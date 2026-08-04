# Source Generated with Decompyle++ (Python version)
# File: repro_07_if_raise_multi_stmt.cpython-311.pyc (Python 3.11)

__doc__ = """R27 repro_07: if-raise with multiple statements after
   def f(x):
       if x is None:
           raise TypeError("None")
       y = x + 1
       z = y * 2
       return z
"""
def f(x):
    if x is None:
        raise TypeError('None')
    y = x + 1
    z = y * 2
    return z
