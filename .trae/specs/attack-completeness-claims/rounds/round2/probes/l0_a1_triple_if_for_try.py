"""AT-02: if x for x try —— 三元嵌套，try 体含 continue/break"""


def a1(xs):
    if xs:
        for x in xs:
            try:
                if x:
                    continue
                else:
                    break
            except ValueError:
                pass
        else:
            print('for-else')
    return 0
