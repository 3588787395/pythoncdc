# Source Generated with Decompyle++ (Python version)
# File: r29_repro07_for_else_func_call.cpython-311.pyc (Python 3.11)

def func_for_else_func_call():
    args = ['a', 'b']
    for arg in args:
        if arg == 'b':
            return 'found_b'
    else:
        print('conversion done')
        return 'not_found'
