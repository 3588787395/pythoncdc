# Source Generated with Decompyle++ (Python version)
# File: c8_unbound_local.pyc (Python 3.11)

def f(cond):
    if cond:
        start = 0
    return start
def main():
    try:
        print(f(False))
        return None
    except BaseException as e:
        print('EXC', type(e).__name__, e)
        return None
