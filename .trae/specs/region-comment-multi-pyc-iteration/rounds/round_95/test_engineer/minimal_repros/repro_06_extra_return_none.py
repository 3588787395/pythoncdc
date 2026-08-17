# R95 minimal repro 06: Extra return None after JUMP_FORWARD
def repro_06(x):
    if x:
        return x
    return None
