def e1(xs):
    return [(a, b) for a in [x] for b in [x] for x in xs]

def e2(xs):
    return [a for a in [xs[0]] for b in [xs[1]]]

def e3(xs):
    return [(a, b) for a in [1, 2] for b in [3, 4]]

def e4(xs):
    return [a for a in [x] for x in xs]
