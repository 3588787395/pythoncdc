# R97 repro 07: return in loop with code after
def repro_07(items, target):
    for item in items:
        if item == target:
            return item
    return None
