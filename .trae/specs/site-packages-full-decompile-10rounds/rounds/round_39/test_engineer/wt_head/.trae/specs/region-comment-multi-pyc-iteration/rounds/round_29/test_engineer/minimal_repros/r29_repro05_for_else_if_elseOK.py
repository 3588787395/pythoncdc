# Source Generated with Decompyle++ (Python version)
# File: r29_repro05_for_else_if_else.cpython-311.pyc (Python 3.11)

def func_for_else_if_else():
    for x in range(10):
        if x == 5:
            break
        continue
    else:
        if x > 3:
            print('big')
        else:
            print('small')
    return x
