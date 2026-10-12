def v1(a, b):
    # B113: 双 for + if 过滤（真迭代协议多 for 子句保持）
    return [i * j for i in a for j in b if i > j]


def v2(m):
    # B113: 嵌套推导（元素位内层推导式 + 外层真 for）
    return [[k for k in row] for row in m]


def v3(a, b, k):
    # B113: 三重 for + 双 if（多子句深一档）
    return [(i, j, w) for i in a for j in b if i > j for w in k if w > i]


def v4(xs):
    # B113: dict 推导双 for + if（种类声明域）
    return {i: j for i in xs for j in xs if i < j}
