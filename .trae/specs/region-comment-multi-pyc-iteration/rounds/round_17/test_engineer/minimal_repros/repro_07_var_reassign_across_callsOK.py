# Source Generated with Decompyle++ (Python version)
# File: repro_07_var_reassign_across_calls.pyc (Python 3.11)

def fetch(factor_id):
    ft = 0
    a = info_get(factor_id, ft)
    ft = 1
    b = info_get(factor_id, ft)
    ft = 2
    c = info_get(factor_id, ft)
    return (a, b, c)
