"""R49 Repro 04: try-except in if-else branch"""
import os

def func(exists):
    if exists:
        try:
            os.unlink('/tmp/test')
            print('deleted')
        except:
            pass
    else:
        print('not exists')
