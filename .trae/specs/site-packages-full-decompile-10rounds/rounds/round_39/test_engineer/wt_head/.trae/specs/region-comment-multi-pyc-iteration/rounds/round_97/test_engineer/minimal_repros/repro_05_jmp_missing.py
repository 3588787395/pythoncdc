# R97 repro 05: JUMP_FORWARD missing after return
def repro_05(x, y):
    if x > 0:
        return x
    if y > 0:
        return y
    return None
