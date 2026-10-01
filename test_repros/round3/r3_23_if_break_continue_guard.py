"""r3_23: 循环内 break/continue 与守卫交互 — if×continue（B2）、if×break、
continue 在 for-else 前后件。"""


def b2_if_continue(items):
    """if×continue（B2 守卫族语料）：then 臂 continue，else 臂顺序体。"""
    out = []
    for x in items:
        if x is None:
            continue
        out.append(x * 2)
    return out


def b2_if_continue_pure(items):
    """then=纯 continue 且 else 含体（_loop_handle_no_exit_successors 对称分支）。"""
    out = []
    k = 0
    while k < len(items):
        v = items[k]
        if v < 0:
            k += 1
            continue
        out.append(v)
        k += 1
    return out


def if_break_then_continue(items):
    """if×break 后接 if×continue：两种终结并存。"""
    out = []
    for x in items:
        if x == "stop":
            break
        if x == "skip":
            continue
        out.append(x)
    else:
        out.append("exhausted")
    return out


def continue_before_and_after_else(m, n):
    """continue 出现在 for-else 前件（体内）与后件（else 体）双向。"""
    acc = []
    for i in range(m):
        if i == 1:
            continue
        for j in range(n):
            if j > i:
                continue
            acc.append((i, j))
        else:
            if i % 2 == 0:
                continue
            acc.append(i)
    return acc
