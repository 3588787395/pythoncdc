# Source Generated with Decompyle++ (Python version)
# File: repro_09_if_raise_else.cpython-311.pyc (Python 3.11)

__doc__ = """R27 repro_09: if-raise with else return
   def f(x):
       if x < 0:
           raise ValueError("negative")
       else:
           return x
"""
def f(x):
    if x < 0:
        raise ValueError('negative')
    return x
