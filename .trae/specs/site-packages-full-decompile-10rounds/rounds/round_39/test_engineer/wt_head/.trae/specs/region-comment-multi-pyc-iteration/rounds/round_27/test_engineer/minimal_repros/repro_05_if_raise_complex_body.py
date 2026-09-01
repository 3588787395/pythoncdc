"""R27 repro_05: if-raise with complex body after
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
        raise ValueError("bad")
    if percent > 1:
        raise ValueError("bad")
    return percent * 100
