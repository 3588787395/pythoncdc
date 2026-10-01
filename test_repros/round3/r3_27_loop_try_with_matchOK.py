# Source Generated with Decompyle++ (Python version)
# File: r3_27_loop_try_with_match.pyc (Python 3.11)

__doc__ = 'r3_27: 循环嵌 try/with/match（B9 消费层关联 — 异常区域包裹循环出口）。'
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
    acc.append('done')
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
            elif i == 5:
                break
                break
            else:
                acc.append(i)
        finally:
            acc.append('f')
    else:
        acc.append('else')
def loop_with_match(m):
    """for 体 with + match，else 收尾。"""
    out = []
    for i in range(m):
        with open_ctx(i) as h:
            v = h
        match v:
            case int(x) if x > 2:
                out.append(x)
                continue
            case str(s):
                out.append(len(s))
                continue
            case _:
                pass
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
