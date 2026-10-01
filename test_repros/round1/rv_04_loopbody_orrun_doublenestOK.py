# Source Generated with Decompyle++ (Python version)
# File: rv_04_loopbody_orrun_doublenest.pyc (Python 3.11)

def f(grid, a, b, c):
    hits = 0
    for row in grid:
        for cell in row:
            if b or c and a:
                hits += 1
                continue
    return hits
