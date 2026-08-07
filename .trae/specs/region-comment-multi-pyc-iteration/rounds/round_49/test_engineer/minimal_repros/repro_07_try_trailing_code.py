"""R49 Repro 07: try-except with trailing code in outer scope"""
import os

def func(exists):
    if exists:
        os.system('chmod 755 /tmp/test')
        try:
            os.unlink('/tmp/test')
            print('deleted')
        except:
            pass
    else:
        print('not exists')
