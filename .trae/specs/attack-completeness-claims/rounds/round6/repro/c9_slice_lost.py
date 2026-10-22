def f(s):
    return s[1:3]


def main():
    try:
        print(f('abcd'))
    except BaseException as e:
        print('EXC', type(e).__name__, e)
