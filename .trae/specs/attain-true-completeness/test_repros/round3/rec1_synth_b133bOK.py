# Source Generated with Decompyle++ (Python version)
# File: rec1_synth_b133b.pyc (Python 3.11)

def s_b133b(xs):
    total = 0
    for i in xs:
        j = i
        while j:
            if j == 2:
                break
            j -= 1
        else:
            total += 100
    return total
