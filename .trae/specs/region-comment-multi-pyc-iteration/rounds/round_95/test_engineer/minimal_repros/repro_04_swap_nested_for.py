# R95 minimal repro 04: SWAP(2)+POP_TOP+RETURN_VALUE with nested for
def repro_04(matrix):
    for row in matrix:
        for cell in row:
            print(cell)
    return None
