# Source Generated with Decompyle++ (Python version)
# File: close_min.pyc (Python 3.11)

def write_pad(fileobj, NUL, BLOCKSIZE):
    fileobj.write(NUL * BLOCKSIZE * 2)
    fileobj.write(NUL * BLOCKSIZE * 3)
