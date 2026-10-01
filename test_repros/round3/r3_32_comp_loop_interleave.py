"""r3_32: 循环 + 生成器/推导式交错 — comprehension 在 loop-else 内、循环内消费生成器。"""


def comp_in_for_else(n):
    """for-else 体内列表推导（子区域在 else_blocks 内）。"""
    evens = []
    for i in range(n):
        if i > 20:
            break
    else:
        evens = [x * 2 for x in range(n) if x % 2 == 0]
    return evens


def genexp_in_while_else(m):
    """while-else 体内生成器表达式求值。"""
    out = []
    k = 0
    while k < m:
        k += 1
        if k == 4:
            break
    else:
        out.append(sum(x * x for x in range(m)))
    return out


def dictcomp_in_loop_body(m):
    """循环体内 dict 推导与循环交错。"""
    acc = {}
    lst = []
    for i in range(m):
        acc = {k: v for k, v in ((i, i * 2), (i + 1, i * 3))}
        lst.append(acc)
        if i == 2:
            break
    else:
        lst.append({j: j for j in range(m)})
    return lst


def nested_comp_loop(m, n):
    """推导式内的 for 与语句级 for 交错，外层带 else。"""
    grid = []
    for i in range(m):
        row = [j * i for j in range(n)]
        grid.append(row)
        if sum(row) > 30:
            break
    else:
        grid.append([i for i in range(n) for _ in range(2)])
    return grid
