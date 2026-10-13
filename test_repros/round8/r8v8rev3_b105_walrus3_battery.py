def v1(f, g, h, i):
    # B105-R2 深度外推：三重嵌套海象实参位值链（深度 3，前缀求和声称域）
    return f((a := g((b := h((c := i()))))), a + b + c)


def v2(x):
    # B105 域邻探查：海象在链式比较条件操作数位（walrus × COPY(2) 链协议交叉）
    if 0 < (n := len(x)) < 10:
        return n
    return 0
