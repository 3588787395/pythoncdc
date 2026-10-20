"""More phantom-prone shapes: merge blocks after no-default matches."""
def f7(x):
    match x:
        case (a, b):
            A(a, b)
    y = 7
    return y

def f8(x):
    match x:
        case (a, b):
            return a
    y = 7
    return y

def f9(x):
    match x:
        case (a, b):
            return a
    return 9

def f10(x):
    match x:
        case (a, b):
            if a:
                R = b
    return 5
