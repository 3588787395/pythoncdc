"""nm01: shallow module negative control."""
A = 1
B = 2
C = A + B


def f():
    return C


class K:
    D = 3


if __name__ == '__main__':
    print(f())
