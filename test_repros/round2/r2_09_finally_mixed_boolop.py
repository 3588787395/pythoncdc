# r2_09 finally 内混合布尔链（与 Round1 判据交互）
# 焦点：finally 块被链续接待收？（任务A 审计项：链判据不得吸收 finally 帧）


def f(a, b, c, log):
    try:
        log.append(a)
    finally:
        if a and b or c:
            log.append("T")
        log.append("F-done")
    return log


def g(a, b, c, acc):
    try:
        acc.append("try")
    finally:
        while a and b or c:
            acc.append("loop")
            break
        assert a and b or c, "r2_09"
    return acc
