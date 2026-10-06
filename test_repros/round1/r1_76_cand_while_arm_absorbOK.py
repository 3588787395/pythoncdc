# Source Generated with Decompyle++ (Python version)
# File: r1_76_cand_while_arm_absorb.pyc (Python 3.11)

def f76(xs, start, end):
    n = 0
    while n < 5:
        n += 1
        if n == 1:
            if n == start:
                continue
            elif n == end:
                pass
        if n is not None:
            print(n)
        else:
            print('none')
        print('tail-in-loop')
