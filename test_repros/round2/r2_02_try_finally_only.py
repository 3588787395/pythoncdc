# r2_02 try/finally-only（无 except）
# 焦点：TRY_FINALLY 形态（台账 :9017-9019 孤儿 finally 帧）


def f(a, b):
    log = []
    try:
        log.append(a)
        if a > b:
            log.append(b)
    finally:
        log.append("end")
    return log


def g(n):
    out = 0
    for i in range(n):
        try:
            if i % 2:
                out += i
        finally:
            out += 1
    return out
