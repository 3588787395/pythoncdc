"""R49 Repro 02: try-except handler dropped - except BaseException"""
import os

def func():
    try:
        os.unlink('/tmp/test')
        print('deleted')
    except BaseException:
        pass
