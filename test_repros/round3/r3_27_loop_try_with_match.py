"""r3_27: 循环嵌 try/with/match（B9 消费层关联 — 异常区域包裹循环出口）。"""


def loop_try_continue(m):
    """try 体 continue（r2_06 关联：循环内 try 体 continue 丢失族）。"""
    acc = []
    for i in range(m):
        try:
            if i % 3 == 1:
                continue
            acc.append(i)
        except ValueError:
            acc.append(-1)
    else:
        acc.append("done")
    return acc


def loop_try_with_break(m):
    """try/finally 包裹循环体 break/continue（r2_14 关联）。"""
    acc = []
    i = 0
    while i < m:
        i += 1
        try:
            if i == 2:
                continue
            if i == 5:
                break
            acc.append(i)
        finally:
            acc.append("f")
    else:
        acc.append("else")
    return acc


def loop_with_match(m):
    """for 体 with + match，else 收尾。"""
    out = []
    for i in range(m):
        with open_ctx(i) as h:
            v = h
        match v:
            case int(x) if x > 2:
                out.append(x)
            case str(s):
                out.append(len(s))
            case _:
                continue
    else:
        out.append(-1)
    return out


def open_ctx(i):
    return _Ctx(i)


class _Ctx:
    def __init__(self, v):
        self.v = v

    def __enter__(self):
        return self.v * 3 if self.v % 2 else str(self.v)

    def __exit__(self, *exc):
        return False
