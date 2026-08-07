# Source Generated with Decompyle++ (Python version)
# File: repro_05_while_else_try.pyc (Python 3.11)

__doc__ = 'R49 Repro 05: while-else with try inside'
import os
import time
def func(path, attempts):
    count = 0
    while count < attempts:
        process_id = open(path, mode='r', encoding='utf-8').readline()
        if process_id != '':
            pass
        else:
            time.sleep(0.001)
            count += 1
    if process_id is not None:
        try:
            os.unlink(path)
            print('deleted')
        except:
            return None
    return None
