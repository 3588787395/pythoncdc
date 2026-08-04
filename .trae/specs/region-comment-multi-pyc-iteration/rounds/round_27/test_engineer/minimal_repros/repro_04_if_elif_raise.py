"""R27 repro_04: if-raise with if-elif pattern
   def f(x):
       if x < 0:
           raise ValueError("negative")
       elif x > 1:
           raise ValueError("too big")
       return x
"""
def f(x):
    if x < 0:
        raise ValueError("negative")
    elif x > 1:
        raise ValueError("too big")
    return x
