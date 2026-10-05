K = {}


def f67(xs):
    for t in xs:
        if t == 'a':
            print('A')
        else:
            if t in K:
                print('B')
            else:
                print('C')
        print('after')
    print('tail')
