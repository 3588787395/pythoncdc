K = {}


def f66(t):
    if t == 'a':
        print('A')
    else:
        if t in K:
            print('B')
        else:
            print('C')
    print('after')
    print('more')
