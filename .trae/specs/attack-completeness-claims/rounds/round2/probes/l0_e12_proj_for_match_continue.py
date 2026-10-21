"""AT-02 for x match 变量分离 2/3: case 体含 continue"""


def e12(v):
    for x in v:
        match x:
            case 0:
                continue
            case _:
                continue
