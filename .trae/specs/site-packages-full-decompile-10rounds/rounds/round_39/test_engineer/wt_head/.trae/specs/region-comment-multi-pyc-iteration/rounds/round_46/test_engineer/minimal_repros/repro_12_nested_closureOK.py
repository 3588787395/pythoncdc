# Source Generated with Decompyle++ (Python version)
# File: repro_12_nested_closure.pyc (Python 3.11)

def make_counter():
    count = 0
    def counter():
        nonlocal count
        count += 1
        return count
    return counter
