# r2_10 try 内混合链 × while/assert/ternary 判据（B6 所有权 vs try 所有权）
# 焦点：try 内混合链被 while/assert/ternary 判据抢走所有权？（任务A 审计项）


def f_while(a, b, c, acc):
    try:
        while a and b or c:
            acc.append(1)
            if len(acc) > 3:
                break
    except TypeError:
        acc.append("te")
    return acc


def f_assert(a, b, c, acc):
    try:
        assert a and b or c, "r2_10"
        acc.append("ok")
    except AssertionError:
        acc.append("ae")
    return acc


def f_ternary(a, b, c, acc):
    try:
        acc.append(2 if a and b or c else 3)
    except TypeError:
        acc.append("te")
    return acc
