def a1(xs, ys):
    return [(x, y) for x in xs for y in ys]

def a2(xs):
    return [(a, b) for x in xs for a in [x] for b in [x]]

def a3(xs):
    return [(a, b) for a in f(xs) for b in g(xs)]

def a4(xs):
    return [z for x in xs for z in h(x)]
