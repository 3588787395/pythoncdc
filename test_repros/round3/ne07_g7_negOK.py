# Source Generated with Decompyle++ (Python version)
# File: ne07_g7_neg.pyc (Python 3.11)

def n_simple_call(a, b):
    return max(a, b)
def n_simple_kwargs(a):
    def sink(x, y=1):
        return x + y
    return sink(a, y=2)
def n_simple_star(a, rest):
    def sink(x, *rs):
        return x + sum(rs)
    return sink(a, *(rest))
