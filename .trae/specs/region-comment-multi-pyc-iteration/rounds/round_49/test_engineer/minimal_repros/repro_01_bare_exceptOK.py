# Source Generated with Decompyle++ (Python version)
# File: repro_01_bare_except.pyc (Python 3.11)

__doc__ = 'R49 Repro 01: try-except handler dropped - bare except'
import os
def func():
    try:
        os.unlink('/tmp/test')
        print('deleted')
    except:
        return None
