"""n3_02（负对照）: 单层 if×continue/if×break 守卫 + 单层 for-else/while-else 有 break。预期全 MATCH。"""


def guard_loop(items):
    out = []
    for x in items:
        if x < 0:
            continue
        if x == 9:
            break
        out.append(x)
    return out


def for_else_with_break(items):
    out = []
    for x in items:
        if x == 7:
            break
        out.append(x)
    else:
        out.append("exhausted")
    return out


def while_else_with_break(n):
    out = []
    k = 0
    while k < n:
        k += 1
        if k == 6:
            break
    else:
        out.append("welse")
    return out


def double_for_plain(m, n):
    out = []
    for i in range(m):
        for j in range(n):
            out.append(i * n + j)
    return out
