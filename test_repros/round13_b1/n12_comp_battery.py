def cb(data):
    n = 3
    a = [[y for y in row] for row in data]
    b = [x for x in data if x > 1 if (m := x) < 9]
    c = {k: v for k, v in data.items() if k in (1, 2)}
    d = (x * 2 for x in data for y in data)
    out = [(last := x) for x in data]
    return a, b, c, d, out, m, last
