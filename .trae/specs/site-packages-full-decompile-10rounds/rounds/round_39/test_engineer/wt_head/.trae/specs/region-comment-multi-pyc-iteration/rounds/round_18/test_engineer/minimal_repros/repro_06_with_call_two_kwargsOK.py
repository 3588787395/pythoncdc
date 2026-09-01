# Source Generated with Decompyle++ (Python version)
# File: repro_06_with_call_two_kwargs.pyc (Python 3.11)

class Ctx:
    def __init__(self, path, mode='r', timeout=0):
        self.path = path
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False
def use_ctx(path):
    with Ctx(path, mode='r', timeout=10) as f:
        return f.path
        return None
