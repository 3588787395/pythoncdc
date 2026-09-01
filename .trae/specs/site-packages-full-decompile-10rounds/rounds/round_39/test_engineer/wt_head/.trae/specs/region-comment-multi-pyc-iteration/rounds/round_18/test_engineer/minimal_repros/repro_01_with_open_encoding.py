# Pattern: with open(path, mode, encoding=) — KW_NAMES keyword-arg drop
# Mirror: strategy.pyc trade_strategy_add `with open(..., 'r', encoding='utf-8')`
# Expected: with open(path, 'r', encoding='utf-8') as f: content = f.read()
# Actual (pre-R18): encoding= dropped -> with open(path, 'r', 'utf-8') (KW_NAMES lost)
# Defect: KW_NAMES ('encoding',) dropped by with-context ctx_expr whitelist
def read_template(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content
# NO-DEFECT after R18 fix
