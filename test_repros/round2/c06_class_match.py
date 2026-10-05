"""c06: class-level match with nested match."""
class CMatch:
    match (1, 2):
        case (a, b):
            PAIR = (a, b)
        case _:
            PAIR = None

    def p(self):
        return self.PAIR


class CMatchDeep:
    match {'k': [1, 2]}:
        case {'k': [x, *rest]} if x:
            for r in rest:
                if r:
                    match r:
                        case int() as n:
                            GOT = n
                        case _:
                            GOT = None
