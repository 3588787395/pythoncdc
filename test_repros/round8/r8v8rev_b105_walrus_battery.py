def v1(f, x, sink):
    # B105: while 条件海象回边重检形（B105-H4 域）
    total = 0
    while (n := f(x)) > 3:
        total += n
        x = x - 1
    return total


def v2(g, h, sink):
    # B105: 嵌套海象实参（B105-H2/H3 域：双副作用对 + 实参位值链）
    return g((a := h((b := h()))), a + b)


def v3(f):
    # B105 负对照：链式赋值 a = b = f()（COPY(1)+STORE+STORE 排除面，须维持等价）
    a = b = f()
    return a, b


def v4(f, xs, sink):
    # B105: 海象在 if 条件位 + 体后续消费（条件位值链保持域）
    if (n := len(xs)) > 3:
        sink.append(n)
    return n
