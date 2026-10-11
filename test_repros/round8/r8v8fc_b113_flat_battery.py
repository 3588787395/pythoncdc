def f1(xs):
    return [t for a in [x] for b in [y] for c in [z] for w in xs]


def f2(xs):
    return [g for a in xs for b in [h(a)]]


def f3(xs):
    return [k for a in xs for b in [[1, 2]]]


def f4(xs):
    return [e for a in xs if a > 0 for b in [a]]


def f5(xs):
    return {b for a in xs for b in [a]}


def f6(xs):
    return {b: c for a in xs for b in [a] for c in [a + 1]}


def f7(xs):
    return (q for a in xs for q in [a * 2])


def f8(xs):
    return [y := a for a in xs]


def f9(xs):
    return [(a, b) for a in [1, 2] for b in [3, 4]]


def f10(xs):
    return [m for a in xs for m in [a, a + 1]]
