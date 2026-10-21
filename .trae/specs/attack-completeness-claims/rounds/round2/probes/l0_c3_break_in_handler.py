"""AT-04: handler 体内 break（B140 形态），break 落点在循环之外"""


def c3(xs):
    for a in xs:
        try:
            print(a)
        except Exception:
            break
    return 0
