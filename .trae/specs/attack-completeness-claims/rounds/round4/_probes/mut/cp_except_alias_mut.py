# Source Generated with Decompyle++ (Python version)
# File: cp_except_alias.pyc (Python 3.11)

class MyErr(Exception):
    pass
def f():
    try:
        raise MyErr()
    except MyErr_MUT:
        return 1
