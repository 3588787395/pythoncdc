# Source Generated with Decompyle++ (Python version)
# File: r1_106_regress_b103_loop_termarm_tailjoin.pyc (Python 3.11)

def f106(host, n, name):
    for x in range(n):
        if host(x):
            host('y')
        else:
            return None
        host('tail')
    else:
        host('end')
        return None
