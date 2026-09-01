# R96 repro 03: return in while loop
def repro_03(n):
    i = 0
    while i < n:
        if i == 5:
            return i
        i += 1
    return None
