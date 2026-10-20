import dis, io

def dump(fn, name):
    buf = io.StringIO()
    dis.dis(fn, file=buf)
    print('=== %s ===' % name)
    print(buf.getvalue())

# form 1: no wildcard, return after match
def f1(x):
    match x:
        case 1:
            A()
    return 5

# form 2: wildcard default with body
def f2(x):
    match x:
        case 1:
            A()
        case _:
            B()
    return 5

# form 3: capture default (case other)
def f3(x):
    match x:
        case 1:
            A()
        case other:
            C(other)
    return 5

# form 4: two literal cases no default
def f4(x):
    match x:
        case 1:
            A()
        case 2:
            B()
    return 5

# form 5: sequence pattern only, no default (x01 shape)
def f5(x):
    match x:
        case (a, b):
            if a:
                R = b
    return 5

dump(f1, 'f1: case 1 only, return after')
dump(f2, 'f2: case 1 + case _ with body')
dump(f3, 'f3: case 1 + case other capture')
dump(f4, 'f4: case 1 + case 2 no default')
dump(f5, 'f5: case (a,b) only, return after')
