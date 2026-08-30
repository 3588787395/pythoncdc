# Source Generated with Decompyle++ (Python version)
# File: t_nested.pyc (Python 3.11)

def nested(algo, datalist):
    try:
        for item in datalist:
            if item:
                try:
                    x = item + 1
                except ValueError:
                    x = 0
        else:
            algo = 1
    finally:
        algo = 2
    return algo
