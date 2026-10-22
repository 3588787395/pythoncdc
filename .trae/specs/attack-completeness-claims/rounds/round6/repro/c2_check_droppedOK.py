# Source Generated with Decompyle++ (Python version)
# File: c2_check_dropped.pyc (Python 3.11)

def f(order, eq):
    if order and not eq:
        raise ValueError('eq must be true if order is true')
    return 'accepted'
def main():
    try:
        print(f(True, False))
        return None
    except BaseException as e:
        print('EXC', type(e).__name__, e)
        return None
