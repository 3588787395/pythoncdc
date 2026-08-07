# Source Generated with Decompyle++ (Python version)
# File: repro_04_try_in_if_else.pyc (Python 3.11)

__doc__ = 'R49 Repro 04: try-except in if-else branch'
import os
def func(exists):
    if exists:
        try:
            os.unlink('/tmp/test')
            print('deleted')
        except:
            return None
    else:
        print('not exists')
