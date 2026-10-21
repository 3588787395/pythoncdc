"""AT-02 for x match 变量分离 3/3: case 体含 with（a2 的 with 子投影在 match 内）"""


def e13(v):
    for x in v:
        match x:
            case 0:
                with open('f') as fh:
                    print(fh)
            case _:
                print('other')
