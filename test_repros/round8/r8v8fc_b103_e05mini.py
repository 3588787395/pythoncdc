
def e05(x):
    try:
        match x:
            case Point(x=0, y=0):
                r = 'origin'
            case Point(x=px, y=py):
                r = px + py
            case _:
                r = 0
    finally:
        pass
    return r
