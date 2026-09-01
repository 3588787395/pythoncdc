# CTRL: with open(path, mode) — no keyword args (no KW_NAMES in bytecode)
# Expected: with open(path, 'r') as f: content = f.read()
# Actual: same (no KW_NAMES to drop; control for with-open pattern)
def read_plain(path):
    with open(path, 'r') as f:
        content = f.read()
    return content
# NO-DEFECT (control, no keywords)
