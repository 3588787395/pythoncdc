"""AT-02 for x match 变量分离 1/3: case 体无 continue"""


def e11(v):
    for x in v:
        match x:
            case 0:
                print('zero')
            case _:
                print('other')
