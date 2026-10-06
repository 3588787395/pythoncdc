# Source Generated with Decompyle++ (Python version)
# File: r1_96_regress_if_for_tail_while_host.pyc (Python 3.11)

def f96(n, items, store):
    while n > 0:
        n -= 1
        if n:
            for k in items:
                store.pop(k)
    if n:
        for k in items:
            store.append(k)
