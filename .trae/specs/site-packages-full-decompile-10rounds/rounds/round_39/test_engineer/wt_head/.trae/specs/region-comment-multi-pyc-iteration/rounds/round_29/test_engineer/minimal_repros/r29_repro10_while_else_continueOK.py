# Source Generated with Decompyle++ (Python version)
# File: r29_repro10_while_else_continue.cpython-311.pyc (Python 3.11)

def func_while_else_continue():
    i = 0
    while i < 10:
        i += 1
        if i % 2 == 0:
            continue
        if i == 7:
            break
    else:
        return 'completed'
    return 'broken'
