# Source Generated with Decompyle++ (Python version)
# File: repro_02_except_baseexception.pyc (Python 3.11)

__doc__ = 'R49 Repro 02: try-except handler dropped - except BaseException'
import os
def func():
    try:
        os.unlink('/tmp/test')
        print('deleted')
    except BaseException:
        return None
