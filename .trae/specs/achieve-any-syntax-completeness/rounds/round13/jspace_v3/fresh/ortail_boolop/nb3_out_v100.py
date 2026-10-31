# Source Generated with Decompyle++ (Python version)
# File: nb3.pyc (Python 3.11)

def f(cls_name, name):
    pattern = chr(95) + str(cls_name) + chr(95) + chr(95)
    pat_len = len(pattern)
    if len(name) > pat_len and name.startswith(pattern) and name[pat_len:pat_len + 1] != [chr(95)] and (name[-1] != chr(95) or name[-2] != chr(95)):
        return True
    return False
