"""R27 repro_03: if-raise with return after (no else)
   def f(x):
       if x < 0:
           raise ValueError("negative")
       return x * 2
"""
def f(x):
    if x < 0:
        raise ValueError("negative")
    return x * 2
