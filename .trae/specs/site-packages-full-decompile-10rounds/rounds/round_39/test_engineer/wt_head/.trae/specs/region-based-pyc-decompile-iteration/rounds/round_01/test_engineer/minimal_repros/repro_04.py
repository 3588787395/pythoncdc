# Repro 04: try/except/else with side-effect in else clause
# Pattern: try/except where else clause modifies variables used after
# When else has statements (not just return), decompiler may merge into try body
def safe_divide(a, b):
    try:
        result = a / b
    except ZeroDivisionError:
        result = 0
    else:
        result = result * 2
    return result
