# rv4 (REVIEW2 variant): B19 - subject is a call-chain tail call / await call


class Cfg:
    def __init__(self, mode):
        self._mode = mode

    def resolve(self):
        return self._mode


class App:
    def __init__(self, mode):
        self.cfg = Cfg(mode)

    def config(self):
        return self.cfg


def tail_call(app):
    """V1: subject = method call chain with tail call."""
    match app.config().resolve():
        case "fast":
            return 1
        case _:
            return 0


def tail_call2(xs):
    """V2: subject = call then subscript (call not at tail but chain)."""
    match sorted(xs)[-1]:
        case 3:
            return "three"
        case _:
            return "no"


def tail_call3(b):
    """V3: subject = bare function call with argument (the B19 core shape)."""
    match list(b):
        case [1, 2]:
            return "twelve"
        case _:
            return "other"


async def await_subject(x):
    """V4: subject = await expression (wrapped in async def)."""
    match await x.wait():
        case 1:
            return "one"
        case _:
            return "no"
