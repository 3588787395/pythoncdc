# Source Generated with Decompyle++ (Python version)
# File: repro_01_if_raise_simple.cpython-311.pyc (Python 3.11)

__doc__ = """R27 repro_01: Simple if-raise pattern
   def f(x):
       if x < 0:
           raise ValueError("negative")
       return x
"""
def f(x):
    if x < 0:
        raise ValueError('negative')
    return x
