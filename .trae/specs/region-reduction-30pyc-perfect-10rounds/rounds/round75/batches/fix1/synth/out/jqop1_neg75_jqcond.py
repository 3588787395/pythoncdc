# Source Generated with Decompyle++ (Python version)
# File: neg75_jqcond.pyc (Python 3.11)

def neg_a(s, flag):
    if flag:
        return 0
    elif '(' in s and ')' not in s:
        return 1
    elif '[' in s or ']' not in s:
        return 2
    else:
        return 3
def neg_c(s):
    hit = 0
    if '(' in s:
        hit += 1
    elif 'x' in s and 'y' in s:
        hit += 2
    if '(' in s and ')' not in s or '[' in s and ']' not in s:
        hit += 4
    return hit
