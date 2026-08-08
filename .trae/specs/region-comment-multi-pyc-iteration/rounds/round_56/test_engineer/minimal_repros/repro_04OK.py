# Source Generated with Decompyle++ (Python version)
# File: repro_04.pyc (Python 3.11)

def repro_04(cond):
    for i in range(10):
        if cond:
            try:
                x = 1
            except:
                continue
