# Source Generated with Decompyle++ (Python version)
# File: r8v8fc_b103_e01mini.pyc (Python 3.11)

def f(x):
    if x > 0:
        match x:
            case 1:
                r = 'one'
            case 2:
                r = 'two'
            case 3 | 4:
                r = 'few'
            case _:
                r = 'many'
    else:
        r = 'neg'
    return r
