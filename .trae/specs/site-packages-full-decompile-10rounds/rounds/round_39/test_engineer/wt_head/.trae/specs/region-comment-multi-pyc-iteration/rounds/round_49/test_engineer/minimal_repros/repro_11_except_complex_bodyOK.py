# Source Generated with Decompyle++ (Python version)
# File: repro_11_except_complex_body.pyc (Python 3.11)

__doc__ = 'R49 Repro 11: except handler with complex body'
import os
def func():
    try:
        result = os.popen('ls /tmp').readlines()
        if len(result) != 0:
            result = [item.strip() for item in result]
            print(result)
    except BaseException:
        print('error occurred')
        result = []
    return result
