# Repro 10: assert statement with error message
# Pattern: assert condition, message - generates LOAD_ASSERTION_ERROR + CALL
# Decompiler may mis-decompile the assert as if/raise combination
def validate(x):
    assert x > 0, "must be positive"
    return x * 2
