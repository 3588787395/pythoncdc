# Source Generated with Decompyle++ (Python version)
# File: c1_tuple_unpack.pyc (Python 3.11)

def f(a, b):
    x, y, z = (a, b, 0)
    return (x, y, z)
def main():
    try:
        print(f(1, 2))
        return None
    except BaseException as e:
        print('EXC', type(e).__name__, e)
        return None
