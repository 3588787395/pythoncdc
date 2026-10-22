def f(cond):
    if cond:
        start = 0
    return start


def main():
    try:
        print(f(False))
    except BaseException as e:
        print('EXC', type(e).__name__, e)
