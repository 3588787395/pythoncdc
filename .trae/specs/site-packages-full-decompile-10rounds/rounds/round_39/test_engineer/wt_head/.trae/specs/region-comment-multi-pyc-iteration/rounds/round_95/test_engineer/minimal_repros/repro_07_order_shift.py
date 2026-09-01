# R95 minimal repro 07: Statement order shift in if body
def repro_07(data, flag):
    if flag:
        x = data[0]
        y = data[1]
        return x + y
    return None
