"""AT-02: for x match x with —— 三元嵌套，case 体含 with + continue"""


def a2(v):
    for x in v:
        match x:
            case 0:
                with open('f') as fh:
                    print(fh)
            case _:
                continue
    else:
        print('else')
