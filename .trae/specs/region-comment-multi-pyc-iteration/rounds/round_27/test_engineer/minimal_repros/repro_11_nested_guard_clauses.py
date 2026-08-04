"""R27 repro_11: Nested if-raise (guard clauses)
   def f(x, y):
       if x is None:
           raise ValueError("x is None")
       if y is None:
           raise ValueError("y is None")
       if x > y:
           return x
       return y
"""
def f(x, y):
    if x is None:
        raise ValueError("x is None")
    if y is None:
        raise ValueError("y is None")
    if x > y:
        return x
    return y
