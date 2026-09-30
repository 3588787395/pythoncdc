# Source Generated with Decompyle++ (Python version)
# File: w2_orchain_plain.pyc (Python 3.11)

def w2(a, b, c, acc):
    if a and b in c:
        if len(c[b]) == 0:
            return -1
        else:
            t = acc
            for x in c[b]:
                t = t + x
            return t
