"""repro_09: if-continue 兄弟语句 — 内层 if true 分支含方法调用（POP_TOP）。

测试 aspect: 内层 if true 分支含方法调用语句（list.append，以 POP_TOP 结尾），
continue 仍为无条件兄弟。验证方法调用 + continue 兄弟的发射顺序。

    for j in range(n):
        if cond:
            if inner_cond:
                result.append(j)
            continue
        result.append(-1)
        break
"""


def f(data):
    result = []
    for j in range(len(data)):
        if data[j] > 0:
            if data[j] > 10:
                result.append(data[j])
            continue
        result.append(-1)
        break
    return result
