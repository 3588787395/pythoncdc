# R95 minimal repro 01: SWAP(2)+POP_TOP+RETURN_VALUE in for loop
# Pattern: expr_stmt; return None in for body

def repro_01(items):
    for item in items:
        print(item)
    return None
