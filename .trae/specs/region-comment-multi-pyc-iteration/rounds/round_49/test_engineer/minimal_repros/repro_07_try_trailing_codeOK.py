# Source Generated with Decompyle++ (Python version)
# File: repro_07_try_trailing_code.pyc (Python 3.11)

__doc__ = 'R49 Repro 07: try-except with trailing code in outer scope'
import os
def func(exists):
    if exists:
        os.system('chmod 755 /tmp/test')
        try:
            os.unlink('/tmp/test')
            print('deleted')
        except:
            return None
    else:
        print('not exists')
