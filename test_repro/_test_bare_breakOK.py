# Source Generated with Decompyle++ (Python version)
# File: _test_bare_break.pyc (Python 3.11)

def test_bare_break(data, key):
    for item in data:
        if item == key:
            break
    else:
        return 'not_found'
    return 'found'
