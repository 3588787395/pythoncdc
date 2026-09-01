# R96 repro 02: return in for loop
def repro_02(items):
    for item in items:
        if item == 0:
            return item
    return None
