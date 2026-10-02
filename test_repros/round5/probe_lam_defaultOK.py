# Source Generated with Decompyle++ (Python version)
# File: probe_lam_default.pyc (Python 3.11)

def fd_stmt(xs):
    f = lambda x: x * 2
    return f
def fd_in_comp(xs):
    return [lambda x: x * 2 for x in xs]
