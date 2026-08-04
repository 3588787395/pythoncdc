"""R27 repro_07: if-raise with multiple statements after
   def f(x):
       if x is None:
           raise TypeError("None")
       y = x + 1
       z = y * 2
       return z
"""
def f(x):
    if x is None:
        raise TypeError("None")
    y = x + 1
    z = y * 2
    return z
