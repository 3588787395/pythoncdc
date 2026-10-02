# Source Generated with Decompyle++ (Python version)
# File: rv4_19_b19_subject_call.pyc (Python 3.11)

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
    if app.config().resolve() == 'fast':
        return 1
    else:
        return 0
def tail_call2(xs):
    """V2: subject = call then subscript (call not at tail but chain)."""
    if sorted(xs)[-1] == 3:
        return 'three'
    else:
        return 'no'
def tail_call3(b):
    """V3: subject = bare function call with argument (the B19 core shape)."""
    match list(b):
        case [1, 2]:
            return 'twelve'
        case _:
            return 'other'
async def await_subject(x):
    """V4: subject = await expression (wrapped in async def)."""
    if await x.wait() == 1:
        return 'one'
    else:
        return 'no'
