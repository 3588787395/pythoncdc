
def e05b(x):
    match x:
        case Point(x=0, y=0):
            r = 'origin'
        case Point(x=px, y=py):
            r = px + py
        case _:
            r = 0
    return r
