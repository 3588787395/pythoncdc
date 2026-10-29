# Source Generated with Decompyle++ (Python version)
# File: er4_guardappend.pyc (Python 3.11)

def f(items):
    result = []
    while True:
        if not items:
            return result
        result.append(items[0])
        items = items[1:]
