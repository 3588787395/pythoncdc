# Source Generated with Decompyle++ (Python version)
# File: r5_02_genexp.pyc (Python 3.11)

def ge_sum_arg(xs):
    return sum((x * x for x in xs))
def ge_max_arg(words):
    return max(((len(w), w) for w in words))
def ge_assigned(xs):
    g = (x + 1 for x in xs)
    return list(g)
def ge_joined(xs):
    return ','.join((str(x) for x in xs))
def ge_nested_arg(mat):
    return sum((sum((y for y in row)) for row in mat))
