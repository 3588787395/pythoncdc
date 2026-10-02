# Source Generated with Decompyle++ (Python version)
# File: r5_01_comp_basic.pyc (Python 3.11)

def lc_basic(xs):
    return [x * 2 for x in xs]
def lc_with_len(words):
    return [len(w) for w in words]
def lc_index_pair(xs):
    return [xs[i] * i for i in range(len(xs))]
def sc_setcomp(xs):
    return {x % 3 for x in xs}
def dc_dictcomp(pairs):
    return {k: v * 2 for k, v in pairs}
def dc_from_keys(words):
    return {w: len(w) for w in words}
