# R97 repro 03: statement order shift in if body
def repro_03(flag, data):
    if flag:
        x = data[0]
        y = data[1]
        return x + y
    return None
