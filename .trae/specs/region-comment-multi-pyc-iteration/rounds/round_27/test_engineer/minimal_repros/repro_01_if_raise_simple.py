"""R27 repro_01: Simple if-raise pattern
   def f(x):
       if x < 0:
           raise ValueError("negative")
       return x
"""
def f(x):
    if x < 0:
        raise ValueError("negative")
    return x
