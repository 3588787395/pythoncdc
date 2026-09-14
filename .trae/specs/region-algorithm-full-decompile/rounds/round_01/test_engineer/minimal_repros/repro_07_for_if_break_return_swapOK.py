# Source Generated with Decompyle++ (Python version)
# File: repro_07_for_if_break_return_swap.cpython-311.pyc (Python 3.11)

def find_item(items, key):
    for item in items:
        if item[0] == key:
            if len(item) > 5:
                return item
