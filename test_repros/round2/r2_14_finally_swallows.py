# r2_14 finally 内 return/break 吞异常形态
# 焦点：finally 帧吞异常（return/break 短路）


def f(n):
    out = []
    for i in range(n):
        try:
            if i == 1:
                raise RuntimeError("boom")
            out.append(i)
        finally:
            if i == 1:
                break
    return out


def g(v):
    try:
        raise ValueError("v")
    finally:
        return "swallow"


def h(v):
    try:
        if v:
            raise RuntimeError("r")
    finally:
        return v * 2
