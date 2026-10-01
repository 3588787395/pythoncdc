# r2_04 深层嵌套：try 嵌 try ≥3 层
# 焦点：嵌套无感（C2 归纳步）——异常区域三层嵌套


def f(a, b, c):
    r = []
    try:
        try:
            try:
                r.append(a // b)
            except ZeroDivisionError:
                r.append("z1")
                raise
        except ZeroDivisionError:
            r.append("z2")
    except Exception:
        r.append("top")
    r.append(c)
    return r
