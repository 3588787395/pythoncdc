# Pattern: with open(encoding=) after if-else-return — mirrors strategy.pyc flow
# Expected: if a: x=a else: return; with open(p,'r',encoding='utf-8') as f: ...
# Actual (pre-R18): encoding= dropped -> with open(p,'r','utf-8') (KW_NAMES lost)
# Defect: KW_NAMES ('encoding',) dropped by with-context ctx_expr whitelist
def read_after_else(path, a):
    if a:
        x = a
    else:
        return None
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content
# NO-DEFECT after R18 fix
