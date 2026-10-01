# r2_05 深层嵌套：try 嵌循环嵌 try
# 焦点：异常区域×循环区域交叠嵌套


def f(n, d):
    acc = 0
    try:
        for i in range(n):
            try:
                acc += d[i] // (i + 1)
            except (KeyError, ZeroDivisionError):
                acc -= 1
    except TypeError:
        acc = -1
    return acc
