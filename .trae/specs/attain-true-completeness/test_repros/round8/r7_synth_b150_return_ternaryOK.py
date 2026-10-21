# Source Generated with Decompyle++ (Python version)
# File: r7_synth_b150_return_ternary.pyc (Python 3.11)

def s_b150_return_ternary(a, b, c, flag):
    return a and b if flag else a < b < c or flag
def s_b150_return_ternary2(a, b, flag):
    return a > 0 if flag else b < 0
