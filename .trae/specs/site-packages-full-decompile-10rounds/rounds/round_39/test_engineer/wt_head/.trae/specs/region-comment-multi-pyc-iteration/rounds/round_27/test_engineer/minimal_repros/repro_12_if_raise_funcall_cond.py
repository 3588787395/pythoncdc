"""R27 repro_12: if-raise with function call in condition
   def f(x):
       if not isinstance(x, int):
           raise TypeError("not int")
       if x < 0:
           raise ValueError("negative")
       return x * 2
"""
def f(x):
    if not isinstance(x, int):
        raise TypeError("not int")
    if x < 0:
        raise ValueError("negative")
    return x * 2
