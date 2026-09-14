# Source Generated with Decompyle++ (Python version)
# File: _test_nested_if_break.pyc (Python 3.11)

def test_nested_if_break(data, key1, key2):
    found = False
    for item in data:
        if item == key1 and key2 is not None:
            found = True
    else:
        found = False
    return found
