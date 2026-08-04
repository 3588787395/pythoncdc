# Source Generated with Decompyle++ (Python version)
# File: repro_12_if_raise_funcall_cond.cpython-311.pyc (Python 3.11)

__doc__ = """R27 repro_12: if-raise with function call in condition
   def f(x):
       if not isinstance(x, int):
           raise TypeError("not int")
       if x < 0:
           raise ValueError("negative")
       return x * 2
"""
def f(x):
    if not isinstance(x, int):
        raise TypeError('not int')
    elif x < 0:
        raise ValueError('negative')
    return x * 2
