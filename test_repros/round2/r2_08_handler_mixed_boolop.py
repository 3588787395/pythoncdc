# r2_08 handler 内混合布尔链（与 Round1 判据交互）
# 焦点：B1b/B6 混合链判据 × handler 上下文（异常区域内的 boolop 所有权）


def f(a, b, c, log):
    try:
        log.append("body")
    except Exception:
        if a and b or c:
            log.append("t1")
        else:
            log.append("f1")
    log.append("end")


def g(a, b, c, log):
    try:
        log.append("body")
    except Exception:
        while a and b or c:
            log.append("w")
            break
    return log
