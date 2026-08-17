# R96 repro 04: multiple return paths
def repro_04(x, y):
    if x > 0:
        return x
    if y > 0:
        return y
    return None
