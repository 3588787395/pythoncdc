import dis, io

def dump(fn, name):
    buf = io.StringIO()
    dis.dis(fn, file=buf)
    print('=== %s ===' % name)
    print(buf.getvalue())

# seq pattern then wildcard default
def g1(x):
    match x:
        case (a, b):
            A(a, b)
        case _:
            B()
    return 5

# seq pattern then capture default
def g2(x):
    match x:
        case (a, b):
            A(a, b)
        case other:
            C(other)
    return 5

# seq then literal case (no default)
def g3(x):
    match x:
        case (a, b):
            A(a, b)
        case 2:
            B()
    return 5

# mapping pattern then wildcard
def g4(x):
    match x:
        case {'k': v}:
            A(v)
        case _:
            B()
    return 5

# class pattern then wildcard
def g5(x):
    match x:
        case Foo(a=1):
            A()
        case _:
            B()
    return 5

dump(g1, 'g1: case (a,b) + case _ body')
dump(g2, 'g2: case (a,b) + case other capture')
dump(g3, 'g3: case (a,b) + case 2 no default')
dump(g4, 'g4: case dict + case _ body')
dump(g5, 'g5: case class + case _ body')
