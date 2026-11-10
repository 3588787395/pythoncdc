# Source Generated with Decompyle++ (Python version)
# File: condleak.pyc (Python 3.11)

def f(src, dst, length=None, bufsize=None):
    bufsize = bufsize or 16384
    if length == 0:
        return None
    else:
        print(bufsize, length)
