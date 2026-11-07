# Source Generated with Decompyle++ (Python version)
# File: E1_chain_else_flatten.pyc (Python 3.11)

def hm(data, weights, n):
    if n < 1:
        raise ValueError('a')
    elif n == 1 and weights is None:
        x = data[0]
        return x
    elif weights is None:
        w = 1
        s = n
    else:
        if weights:
            weights = list(weights)
        if len(weights) != n:
            raise ValueError('c')
        s = 2
    return s
