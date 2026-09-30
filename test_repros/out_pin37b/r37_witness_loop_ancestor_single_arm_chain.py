# Source Generated with Decompyle++ (Python version)
# File: r37_witness_loop_ancestor_single_arm_chain.pyc (Python 3.11)

__doc__ = 'r37 battery case'
from time import sleep
def s(n):
    return n
def ok():
    return True
def f(x):
    return x
def tick(dt):
    while True:
        if not ok():
            sleep(60)
            continue
        if dt == 'a':
            if '08:30' <= dt < '08:59' or '12:30' <= dt < '12:59':
                s(60)
        elif f(dt):
            pass
