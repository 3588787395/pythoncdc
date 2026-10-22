# Source Generated with Decompyle++ (Python version)
# File: c9_slice_lost.pyc (Python 3.11)

def f(s):
    return s[1:3]
def main():
    try:
        print(f('abcd'))
        return None
    except BaseException as e:
        print('EXC', type(e).__name__, e)
        return None
