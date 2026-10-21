"""AT-04: for-else 位于 match case 体内"""


def b2(v):
    match v:
        case [x]:
            for i in range(x):
                print(i)
            else:
                print('else')
        case _:
            pass
