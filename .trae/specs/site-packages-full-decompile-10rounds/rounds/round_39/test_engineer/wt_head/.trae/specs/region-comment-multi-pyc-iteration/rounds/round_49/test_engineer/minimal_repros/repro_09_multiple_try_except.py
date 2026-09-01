"""R49 Repro 09: multiple try-except in sequence"""
import os

def func():
    try:
        os.unlink('/tmp/a')
    except:
        pass
    try:
        os.unlink('/tmp/b')
    except:
        pass
