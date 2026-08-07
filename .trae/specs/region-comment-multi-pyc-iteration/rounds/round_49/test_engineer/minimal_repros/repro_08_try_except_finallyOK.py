# Source Generated with Decompyle++ (Python version)
# File: repro_08_try_except_finally.pyc (Python 3.11)

__doc__ = 'R49 Repro 08: try-except-finally with pass in except'
import os
def func():
    try:
        os.unlink('/tmp/test')
    except:
        pass
    finally:
        print('done')
