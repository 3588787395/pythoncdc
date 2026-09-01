# CTRL: call with kwarg but NOT in with-statement (aes_encrypt pattern)
# Expected: result = f(content, key=k, iv=v) — kwarg preserved (not with-context)
# Actual: same (non-with CALL path already handles KW_NAMES; control)
def encrypt(content, k, v):
    return f(content, key=k, iv=v)
# NO-DEFECT (control, non-with call with kwargs)
