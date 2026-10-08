# Source Generated with Decompyle++ (Python version)
# File: r3_b130_3_for_posttry.pyc (Python 3.11)

def h(xs):
    total = 0
    for x in xs:
        try:
            total += int(x)
        except ValueError:
            total += 1
        print(total)
    return total
