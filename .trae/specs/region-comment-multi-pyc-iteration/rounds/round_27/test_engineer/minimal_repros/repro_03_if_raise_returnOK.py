# Source Generated with Decompyle++ (Python version)
# File: repro_03_if_raise_return.cpython-311.pyc (Python 3.11)

__doc__ = """R27 repro_03: if-raise with return after (no else)
   def f(x):
       if x < 0:
           raise ValueError("negative")
       return x * 2
"""
def f(x):
    if x < 0:
        raise ValueError('negative')
    return x * 2
