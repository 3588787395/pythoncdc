# Source Generated with Decompyle++ (Python version)
# File: repro_10_if_raise_in_loop.cpython-311.pyc (Python 3.11)

__doc__ = """R27 repro_10: if-raise inside loop
   def f(items):
       for item in items:
           if item < 0:
               raise ValueError("negative")
           print(item)
"""
def f(items):
    for item in items:
        if item < 0:
            raise ValueError('negative')
        print(item)
