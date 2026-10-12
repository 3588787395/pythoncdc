# Source Generated with Decompyle++ (Python version)
# File: r8v8rev_b105_walrus_battery.pyc (Python 3.11)

def v1(f, x, sink):
    total = 0
    while (n := f(x)) > 3:
        total += n
        x = x - 1
    return total
def v2(g, h, sink):
    a = h((b := h()))
def v3(f):
    a = b = f()
    return (a, b)
def v4(f, xs, sink):
    if (n := len(xs)) > 3:
        sink.append(n)
    return n
