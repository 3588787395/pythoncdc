"""R49 Repro 03: nested try-except with both handlers"""
import os

def func():
    try:
        try:
            os.unlink('/tmp/test')
            print('inner')
        except BaseException:
            pass
    except:
        pass
