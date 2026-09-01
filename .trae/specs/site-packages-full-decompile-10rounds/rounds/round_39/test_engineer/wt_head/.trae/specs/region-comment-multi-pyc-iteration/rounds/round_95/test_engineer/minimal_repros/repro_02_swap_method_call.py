# R95 minimal repro 02: SWAP(2)+POP_TOP+RETURN_VALUE with method call
def repro_02(data):
    for key in data:
        data[key].append(1)
    return None
