def f(order, eq):
    if order and not eq:
        raise ValueError('eq must be true if order is true')
    return 'accepted'


def main():
    try:
        print(f(True, False))
    except BaseException as e:
        print('EXC', type(e).__name__, e)
