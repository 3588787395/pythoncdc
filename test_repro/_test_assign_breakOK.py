# Source Generated with Decompyle++ (Python version)
# File: _test_assign_break.pyc (Python 3.11)

def test_assign_before_break(data, key):
    found = False
    for item in data:
        if item == key:
            found = True
    else:
        found = False
    return found
