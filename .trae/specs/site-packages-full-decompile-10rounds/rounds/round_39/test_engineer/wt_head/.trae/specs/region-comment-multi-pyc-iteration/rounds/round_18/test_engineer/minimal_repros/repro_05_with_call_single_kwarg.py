# Pattern: with ctx(path, kw=v) — custom context-manager call with single keyword
# Expected: with ctx(path, mode='r') as f: ...
# Actual (pre-R18): keyword dropped -> with ctx(path, 'r') (KW_NAMES lost)
# Defect: KW_NAMES ('mode',) dropped by with-context ctx_expr whitelist
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
# NO-DEFECT after R18 fix
