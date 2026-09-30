# Source Generated with Decompyle++ (Python version)
# File: r76_b1b_orarm.pyc (Python 3.11)

def neg_a(s, flag):
    if flag:
        return 0
    elif '(' in s and ')' not in s:
        return 1
    elif '[' in s or ']' not in s:
        return 2
    else:
        return 3
def neg_b(a, b, c):
    total = 0
    if a and b:
        total += 1
    if b or c:
        total += 2
    if not (a and b):
        total += 4
    return total
