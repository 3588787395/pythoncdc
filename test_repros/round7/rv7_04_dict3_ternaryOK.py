# Source Generated with Decompyle++ (Python version)
# File: rv7_04_dict3_ternary.pyc (Python 3.11)

def dict3_two_ternary(v1, v2, v3, k1, k2, c1, c2):
    return {'a': v1 if c1 else v2, 'b': k1 if c2 else k2, 'c': v3}
def dict3_nested_value(v1, v2, xs, flag, c1):
    v1 if c1 else v2
