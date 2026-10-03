# Source Generated with Decompyle++ (Python version)
# File: r7_10_chain_compare_calls.pyc (Python 3.11)

__doc__ = 'R7-10 链式比较求值语义面（链内调用/下标/布尔组合）。'
def c_call_chain(a, b, c):
    return len(a) < len(b) < len(c)
def c_call_chain_mixed(a, b):
    return a.count(1) <= b.count(1) != -1
def c_index_chain(xs, ys, zs, i, j, k):
    return xs[i] < ys[j] < zs[k]
def c_index_call_chain(xs, i, ys, j):
    return xs[i] < ys.pop(j) < 10
def c_chain_and_combo(a, b, c, d):
    return a < b < c
def c_chain_or_and_combo(a, b, c, d, e):
    return a < b < c or d < e < a
def c_method_chain(obj, other):
    return obj.key < other.key < obj.limit
