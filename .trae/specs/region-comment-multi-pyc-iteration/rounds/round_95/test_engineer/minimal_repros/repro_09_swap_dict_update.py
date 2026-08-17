# R95 minimal repro 09: SWAP(2)+POP_TOP+RETURN_VALUE with dict update
def repro_09(data):
    for key, val in data.items():
        data[key] = val * 2
    return None
