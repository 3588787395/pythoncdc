# Pattern: with open(path, mode, errors=, encoding=) — two KW_NAMES (reversed order)
# Expected: with open(path, 'r', errors='ignore', encoding='utf-8') as f: ...
# Actual (pre-R18): both keywords dropped -> positional args (KW_NAMES lost)
# Defect: KW_NAMES ('errors', 'encoding') dropped by with-context ctx_expr whitelist
def read_ignore(path):
    with open(path, 'r', errors='ignore', encoding='utf-8') as f:
        return f.read()
# NO-DEFECT after R18 fix
