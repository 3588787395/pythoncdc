# Source Generated with Decompyle++ (Python version)
# File: repro_02.pyc (Python 3.11)

def repro_02():
    for f in (1, 2, 3):
        for i in range(10):
            try:
                x = f * i
            except:
                continue
