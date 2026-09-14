# Source Generated with Decompyle++ (Python version)
# File: _test_while_assign_break.pyc (Python 3.11)

def while_assign_break(limit, exit_val):
    found = False
    count = 0
    while count < limit:
        if count == exit_val:
            found = True
            break
        count += 1
    else:
        found = False
    return found
