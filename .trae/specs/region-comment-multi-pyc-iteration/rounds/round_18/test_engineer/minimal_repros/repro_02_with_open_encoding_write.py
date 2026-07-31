# Pattern: with open(path, mode, encoding=) — KW_NAMES keyword-arg drop (write mode)
# Expected: with open(path, 'w', encoding='gbk') as f: f.write(s); return len(s)
# Actual (pre-R18): encoding= dropped -> with open(path, 'w', 'gbk') (KW_NAMES lost)
# Defect: KW_NAMES ('encoding',) dropped by with-context ctx_expr whitelist
def write_text(path, s):
    with open(path, 'w', encoding='gbk') as f:
        f.write(s)
    return len(s)
# NO-DEFECT after R18 fix
