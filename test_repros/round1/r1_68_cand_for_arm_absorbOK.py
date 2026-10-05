# Source Generated with Decompyle++ (Python version)
# File: r1_68_cand_for_arm_absorb.pyc (Python 3.11)

def f68(xs, start, end):
    for n in xs:
        if n[0] == 1:
            if n[0] == start:
                continue
            elif n[0] == end:
                if n is not None:
                    print(n)
                else:
                    print('none')
        print('tail-in-loop')
    print('after-loop')
