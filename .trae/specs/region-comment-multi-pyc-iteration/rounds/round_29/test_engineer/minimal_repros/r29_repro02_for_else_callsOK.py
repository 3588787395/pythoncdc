# Source Generated with Decompyle++ (Python version)
# File: r29_repro02_for_else_calls.cpython-311.pyc (Python 3.11)

def func_for_else_with_calls():
    for item in (1, 2, 3):
        if item == 2:
            return 'found'
    else:
        print('not found')
        return 'not found'
