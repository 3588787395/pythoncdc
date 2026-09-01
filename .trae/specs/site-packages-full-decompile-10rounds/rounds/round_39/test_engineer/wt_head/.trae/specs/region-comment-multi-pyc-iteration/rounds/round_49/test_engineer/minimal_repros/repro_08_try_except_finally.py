"""R49 Repro 08: try-except-finally with pass in except"""
import os

def func():
    try:
        os.unlink('/tmp/test')
    except:
        pass
    finally:
        print('done')
