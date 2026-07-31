# Pattern: with ctx(path, kw1=v1, kw2=v2) — custom ctx-manager with two keywords
# Expected: with Ctx(path, mode='r', timeout=10) as f: ...
# Actual (pre-R18): both keywords dropped -> positional args (KW_NAMES lost)
# Defect: KW_NAMES ('mode', 'timeout') dropped by with-context ctx_expr whitelist
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
# NO-DEFECT after R18 fix
