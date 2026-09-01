# R95 minimal repro 05: SWAP(2)+COPY(2)+COMPARE_OP chained comparison
def repro_05(a, b, c):
    if a < b < c:
        return True
    return False
