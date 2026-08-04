# Source Generated with Decompyle++ (Python version)
# File: repro_02_if_raise_chain.cpython-311.pyc (Python 3.11)

__doc__ = """R27 repro_02: Two if-raise guards in sequence (the api_stock pattern)
   def f(x):
       if x < 0:
           raise ValueError("negative")
       if x > 1:
           raise ValueError("too big")
       return x
"""
def f(x):
    if x < 0:
        raise ValueError('negative')
    elif x > 1:
        raise ValueError('too big')
    return x
