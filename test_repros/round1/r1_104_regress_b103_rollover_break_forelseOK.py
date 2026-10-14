# Source Generated with Decompyle++ (Python version)
# File: r1_104_regress_b103_rollover_break_forelse.pyc (Python 3.11)

def f104(host, n, name):
    for x in range(n - 1, 0, -1):
        src = '%s.%d' % (name, x)
        if host(src):
            break
    else:
        host(name)
        return None
    for i in range(x, 0, -1):
        host(i)
    host(name)
