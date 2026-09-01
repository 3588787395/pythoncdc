# Source Generated with Decompyle++ (Python version)
# File: repro_05_with_call_single_kwarg.pyc (Python 3.11)

class Ctx:
    def __init__(self, path, mode='r'):
        self.path = path
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False
def use_ctx(path):
    with Ctx(path, mode='r') as f:
        return f.path
        return None
