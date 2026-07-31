# CTRL: with ctx — bare context manager (no call, no KW_NAMES)
# Expected: with Ctx() as f: pass; return result (variable return after with)
# Actual: same (no CALL/KW_NAMES in context_expr; control)
class Ctx:
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False
def use_bare():
    with Ctx() as f:
        pass
    return f
# NO-DEFECT (control, no call kwargs)
