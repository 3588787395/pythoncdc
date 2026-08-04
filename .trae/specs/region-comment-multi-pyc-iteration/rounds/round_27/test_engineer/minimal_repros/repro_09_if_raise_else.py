"""R27 repro_09: if-raise with else return
   def f(x):
       if x < 0:
           raise ValueError("negative")
       else:
           return x
"""
def f(x):
    if x < 0:
        raise ValueError("negative")
    else:
        return x
