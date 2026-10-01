# r2_07 try 体含 with/匹配
# 焦点：try 与 with/match 区域交叠


def f(path, mode, x):
    res = []
    try:
        with open(path, mode) as fh:
            res.append(fh.read(1))
        match x:
            case {"k": v}:
                res.append(v)
            case [first, *rest]:
                res.append((first, len(rest)))
            case str() as s:
                res.append(s.upper())
            case _:
                res.append(0)
    except (OSError, TypeError):
        res.append("err")
    return res
