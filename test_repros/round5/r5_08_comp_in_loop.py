def l_for_break(xs, limit):
    out = []
    for i in range(len(xs)):
        row = [x * i for x in xs]
        out.append(row)
        if len(out) >= limit:
            break
    return out


def l_for_continue(xs):
    out = []
    for x in xs:
        if x < 0:
            continue
        out.extend([x * 2 for x in range(x)])
    return out


def l_while_comp(xs):
    out = []
    i = 0
    while i < len(xs):
        out += [x + i for x in xs]
        i += 1
    return out


def l_if_branch(xs, flag):
    if flag:
        return [x * 3 for x in xs]
    else:
        return [x for x in xs if x]


def l_comp_guard_break(mat, thr):
    res = []
    for chunk in mat:
        total = sum(v for v in chunk)
        if total > thr:
            break
        res.append(total)
    return res


def l_nested_loop_comp(mat):
    out = []
    for row in mat:
        for v in row:
            out.append([v + w for w in row])
    return out
