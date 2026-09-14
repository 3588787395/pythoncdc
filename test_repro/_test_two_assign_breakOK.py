# Source Generated with Decompyle++ (Python version)
# File: _test_two_assign_break.pyc (Python 3.11)

def test_two_assign_break(data, key):
    found = False
    value = None
    for item in data:
        if item == key:
            found = True
            value = item
    else:
        found = False
    return found
