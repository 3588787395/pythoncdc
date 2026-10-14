# Source Generated with Decompyle++ (Python version)
# File: r3_b04_andor_family_chain.pyc (Python 3.11)

def f(a, b, c, d):
    if a and b or c and d:
        need = 0
    else:
        need = 1
    for t in TYPES:
        use(need, t)
    return need
