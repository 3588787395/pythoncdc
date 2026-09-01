# Source Generated with Decompyle++ (Python version)
# File: repro_09.pyc (Python 3.11)

def repro_09():
    for i in range(10):
        try:
            x = 1
        except ValueError:
            continue
        except TypeError:
            continue
