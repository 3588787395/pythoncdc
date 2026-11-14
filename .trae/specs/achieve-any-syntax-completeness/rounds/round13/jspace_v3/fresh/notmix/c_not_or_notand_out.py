# Source Generated with Decompyle++ (Python version)
# File: c_not_or_notand.pyc (Python 3.11)

def f(host, port, names):
    if host:
        if not port and host in names:
            return 1
        return 0
