# Source Generated with Decompyle++ (Python version)
# File: c_not_or_notand.pyc (Python 3.11)

def f(host, port, names):
    if not host or not port and host in names:
        return 1
    else:
        return 0
