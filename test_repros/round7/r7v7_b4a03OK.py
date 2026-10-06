# Source Generated with Decompyle++ (Python version)
# File: r7v7_b4a03.pyc (Python 3.11)

def b4a03_shallow(flag):
    if flag:
        try:
            flag = not flag
        finally:
            flag = not flag
def b4a03_deep(flag, n):
    while n > 0:
        if flag:
            try:
                flag = not flag
            finally:
                flag = not flag
    return flag
