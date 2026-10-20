# Source Generated with Decompyle++ (Python version)
# File: r7_synth_b148_slice_ternary.pyc (Python 3.11)

def s_b148_slice_ternary(xs, a, b):
    for i in range(3):
        if i and i:
            return xs[a + 1:b * 2] + xs[a if b else 0:3]
    return 0
def s_b148_slice_ternary2(xs, a, b):
    for i in range(3):
        if i and i:
            return xs[a if b else 1:3]
    return 0
