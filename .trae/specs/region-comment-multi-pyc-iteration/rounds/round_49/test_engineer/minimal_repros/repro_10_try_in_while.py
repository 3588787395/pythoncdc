"""R49 Repro 10: try-except inside while loop body"""
import os

def func(path, attempts):
    count = 0
    while count < attempts:
        try:
            data = open(path).read()
            if data != '':
                pass
            else:
                count += 1
        except:
            pass
