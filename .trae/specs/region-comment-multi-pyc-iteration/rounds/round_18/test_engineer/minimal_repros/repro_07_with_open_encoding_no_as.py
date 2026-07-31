# Pattern: with open(path, mode, encoding=) — no `as` binding (POP_TOP variant)
# Expected: with open(path, 'r', encoding='utf-8'): pass; return status
# Actual (pre-R18): encoding= dropped -> with open(path, 'r', 'utf-8') (KW_NAMES lost)
# Defect: KW_NAMES ('encoding',) dropped by with-context ctx_expr whitelist
def read_no_as(path):
    with open(path, 'r', encoding='utf-8'):
        pass
    return path
# NO-DEFECT after R18 fix
