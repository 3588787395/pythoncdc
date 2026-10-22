def f(a, b):
    x, y, z = a, b, 0
    return (x, y, z)


def main():
    try:
        print(f(1, 2))
    except BaseException as e:
        print('EXC', type(e).__name__, e)
