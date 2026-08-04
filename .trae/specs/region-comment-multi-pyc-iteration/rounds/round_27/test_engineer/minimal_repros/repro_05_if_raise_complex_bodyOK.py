# Source Generated with Decompyle++ (Python version)
# File: repro_05_if_raise_complex_body.cpython-311.pyc (Python 3.11)

__doc__ = """R27 repro_05: if-raise with complex body after
   def f(percent):
       percent = float(percent)
       if percent < 0:
           raise ValueError("bad")
       if percent > 1:
           raise ValueError("bad")
       return percent * 100
"""
def f(percent):
    percent = float(percent)
    if percent < 0:
        raise ValueError('bad')
    elif percent > 1:
        raise ValueError('bad')
    return percent * 100
