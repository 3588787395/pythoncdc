def m(x, Point):
    match x:
        case [a, b]: return a
        case [a, *rest]: return rest
        case {"k": v}: return v
        case Point(x=px, y=py): return px
        case _: return None
