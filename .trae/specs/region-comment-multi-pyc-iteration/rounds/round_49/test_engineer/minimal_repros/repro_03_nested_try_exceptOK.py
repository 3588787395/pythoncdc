# Source Generated with Decompyle++ (Python version)
# File: repro_03_nested_try_except.pyc (Python 3.11)

__doc__ = 'R49 Repro 03: nested try-except with both handlers'
import os
def func():
    try:
        try:
            os.unlink('/tmp/test')
            print('inner')
        except BaseException:
            pass
    except:
        return None
