"""R2 合成变体 F2a（e02 宿主族 item 7 交叉变体，非语料）。"""


def u_handler(a, b, c):
    try:
        for i in range(3):
            if i:
                return (a or b) and c
    except KeyError:
        return (a or b) and c if a else -2
    return 0


def u_with_host(a, b, c):
    class CM:
        def __enter__(self):
            return self

        def __exit__(self, *e):
            return False
    with CM() as cm:
        for j in range(2):
            if j:
                return a or b and c
    return 0
