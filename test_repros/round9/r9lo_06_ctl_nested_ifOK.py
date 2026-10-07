# Source Generated with Decompyle++ (Python version)
# File: r9lo_06_ctl_nested_if.pyc (Python 3.11)

def r9lo_06_ctl_nested_if(a, b, out):
    if a and b:
        out.add(a)
    if b and a == 1:
        out.add(b)
    return out
