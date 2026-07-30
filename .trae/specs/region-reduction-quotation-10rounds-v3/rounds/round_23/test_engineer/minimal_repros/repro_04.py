"""repro_04: if-continue 兄弟语句 — 内层 if true 分支含多条语句。

测试 aspect: 内层 if 的 true 分支含多条语句（赋值 + 方法调用），continue 仍为
无条件兄弟。验证多语句 true 分支不影响 continue 兄弟发射。

    for j in range(n):
        if outer_cond:
            if inner_cond:
                x = 1
                y = 2
            continue
        z = j
        break
"""


def f(data):
    result = {}
    for j in range(len(data)):
        if data[j] > 0:
            if j % 2 == 0:
                result['a'] = j
                result['b'] = j * 2
            continue
        result['skip'] = j
        break
    return result
