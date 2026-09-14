# Source Generated with Decompyle++ (Python version)
# File: _test_method_break.pyc (Python 3.11)

def test_method_before_break(data, key):
    result = []
    for item in data:
        if item == key:
            result.append(item)
    else:
        result.append('not_found')
    return result
