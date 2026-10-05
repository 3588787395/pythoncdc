# Source Generated with Decompyle++ (Python version)
# File: rv3_07_b89_trim_overtrim.pyc (Python 3.11)

def ternary_then_if(c, d):
    r = 1 if c else 2
    if d:
        r = r + 10
    else:
        r = r - 10
    return r
def ternary_then_cmp(c, d):
    r = 'big' if c else 'small'
    flag = d > 3
    return (r, flag)
def ternary_chain_then_while(c, d):
    a = 1 if c else 3
    b = 4 and 6 if d else 7
    n = 0
    while n < b:
        n = n + 1
    return (a, n)
