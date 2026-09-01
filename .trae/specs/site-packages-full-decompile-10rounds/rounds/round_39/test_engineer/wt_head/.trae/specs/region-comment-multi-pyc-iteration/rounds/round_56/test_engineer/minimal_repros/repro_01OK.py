# Source Generated with Decompyle++ (Python version)
# File: repro_01.pyc (Python 3.11)

def repro_01():
    for i in range(10):
        try:
            x = 1
        except:
            continue
    else:
        return True
