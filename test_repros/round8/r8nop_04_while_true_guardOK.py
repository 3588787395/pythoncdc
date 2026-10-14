# Source Generated with Decompyle++ (Python version)
# File: r8nop_04_while_true_guard.pyc (Python 3.11)

def n8p04(a, lim):
    count = 1
    while True:
        if tick() - a <= lim:
            if g(count):
                break
            count += 1
        else:
            break
    return count
