def f(a, b):
    if a and b:
        return 'both'
    return 'not-both'


def main():
    print(f(True, True))
    print(f(True, False))
