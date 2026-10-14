# Source Generated with Decompyle++ (Python version)
# File: r9lo_04_ctl_plain_or.pyc (Python 3.11)

def r9lo_04_ctl_plain_or(a, b, out):
    if a == 1 or b == 2:
        out.add(a)
    if a == 3 or not b > 4:
        out.add(b)
    return out
