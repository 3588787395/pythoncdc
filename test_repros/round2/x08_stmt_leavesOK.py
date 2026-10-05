# Source Generated with Decompyle++ (Python version)
# File: x08_stmt_leaves.pyc (Python 3.11)

__doc__ = 'x08: statement-form leaves in deep hosts.'
def assert_leaf():
    for i in range(1):
        while i and i:
            if not i:
                pass
    return 1
def raise_leaf():
    try:
        for i in range(1):
            if i:
                break
            continue
        try:
            raise ValueError(i)
        finally:
            F = i
    except ValueError:
        R = 1
    return 2
def return_leaf():
    for i in range(1):
        while i and i:
            if i:
                return i
def delete_leaf():
    obj = [1, 2, 3]
    for i in range(1):
        if i:
            try:
                del obj[0]
            finally:
                pass
    return obj
def assign_leaves():
    out = []
    for i in range(1):
        if i:
            out += [x for x in range(2)]
            aug = 0
            aug += i
            ann = i
            ann += aug
            out.append((aug, ann))
    return out
def import_leaf():
    global IMPORT_G
    for i in range(1):
        if i:
            with _A():
                import json as _j
                IMPORT_G = _j
    return 3
