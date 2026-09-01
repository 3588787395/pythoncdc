# Source Generated with Decompyle++ (Python version)
# File: repro_10_ctrl_with_simple_ctx.pyc (Python 3.11)

class Ctx:
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False
def use_bare():
    with Ctx() as f:
        pass
    return f
