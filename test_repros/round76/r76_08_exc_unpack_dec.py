# Source Generated with Decompyle++ (Python version)
# File: r76_08_exc_unpack.pyc (Python 3.11)

import sys
import os
def f():
    try:
        return work()
        return None
    except BaseException as x:
        log('error here: ' + str(x))
        print('print here')
        exc_type = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print('exc info:', exc_type, fname, exc_tb.tb_lineno)
        log('real data error: ' + str(x))
        return None
