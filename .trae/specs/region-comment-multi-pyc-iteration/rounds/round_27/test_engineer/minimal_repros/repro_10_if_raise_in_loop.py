"""R27 repro_10: if-raise inside loop
   def f(items):
       for item in items:
           if item < 0:
               raise ValueError("negative")
           print(item)
"""
def f(items):
    for item in items:
        if item < 0:
            raise ValueError("negative")
        print(item)
