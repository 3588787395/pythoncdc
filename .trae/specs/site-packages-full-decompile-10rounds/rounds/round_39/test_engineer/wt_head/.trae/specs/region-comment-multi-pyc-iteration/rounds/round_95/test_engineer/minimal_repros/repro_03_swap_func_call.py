# R95 minimal repro 03: SWAP(2)+POP_TOP+RETURN_VALUE with function call
def repro_03(items):
    for item in items:
        process(item)
    return None

def process(x):
    pass
