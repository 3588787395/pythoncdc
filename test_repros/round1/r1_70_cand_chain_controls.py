K = {}


def f70(t):
    if t == 'a':
        print('A')
    elif t in K:
        print('B')
    else:
        print('C')
    print('after')


def f71(t):
    if t == 'a':
        print('A')
    else:
        if t in K:
            print('B')
        else:
            print('C')
