"""R27 repro_06: if-not pattern that should NOT be inverted
   Source: if not x < 0: body
   This is different from if x < 0: raise; body
"""
def f(x):
    if not x < 0:
        return x * 2
    return -x
