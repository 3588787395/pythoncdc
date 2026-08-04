"""R27 repro_02: Two if-raise guards in sequence (the api_stock pattern)
   def f(x):
       if x < 0:
           raise ValueError("negative")
       if x > 1:
           raise ValueError("too big")
       return x
"""
def f(x):
    if x < 0:
        raise ValueError("negative")
    if x > 1:
        raise ValueError("too big")
    return x
