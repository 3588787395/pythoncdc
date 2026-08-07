# Source Generated with Decompyle++ (Python version)
# File: repro_09_multiple_try_except.pyc (Python 3.11)

__doc__ = 'R49 Repro 09: multiple try-except in sequence'
import os
def func():
    try:
        os.unlink('/tmp/a')
    except:
        pass
    try:
        os.unlink('/tmp/b')
    except:
        return None
