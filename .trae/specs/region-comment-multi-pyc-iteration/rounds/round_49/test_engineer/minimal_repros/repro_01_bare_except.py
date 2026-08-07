"""R49 Repro 01: try-except handler dropped - bare except"""
import os

def func():
    try:
        os.unlink('/tmp/test')
        print('deleted')
    except:
        pass
