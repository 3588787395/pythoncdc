# R95 minimal repro 10: SWAP(2)+POP_TOP+RETURN_VALUE with list append
def repro_10(items):
    result = []
    for item in items:
        result.append(item)
    return None
