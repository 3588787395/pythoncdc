# Source Generated with Decompyle++ (Python version)
# File: minrepro_01.pyc (Python 3.11)

def for_else_with_continue(data):
    result = 0
    for item in data:
        if item > 0:
            result += item
    result = -1
    return result
