# Source Generated with Decompyle++ (Python version)
# File: repro_r28_02_and_none_chain_two_branches.pyc (Python 3.11)

def f(a, b, params):
    if a is not None and b is None:
        params['a'] = a
        return None
    elif a is None and b is not None:
        params['b'] = b
        return None
