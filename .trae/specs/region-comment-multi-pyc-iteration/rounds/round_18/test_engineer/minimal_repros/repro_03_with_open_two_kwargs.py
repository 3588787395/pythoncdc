# Pattern: with open(path, mode, encoding=, newline=) — two KW_NAMES keywords
# Expected: with open(path, 'r', encoding='utf-8', newline='\n') as f: ...
# Actual (pre-R18): both keywords dropped -> positional args (KW_NAMES lost)
# Defect: KW_NAMES ('encoding', 'newline') dropped by with-context ctx_expr whitelist
def read_newline(path):
    with open(path, 'r', encoding='utf-8', newline='\n') as f:
        return f.read()
# NO-DEFECT after R18 fix
