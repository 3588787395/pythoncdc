# Repro 12: try/except with else + finally
# Pattern: try/except/else/finally - complex exception handling with all clauses
# Decompiler may lose else clause or misorder finally cleanup
def compute(x, y):
    result = None
    try:
        result = x / y
    except ZeroDivisionError:
        result = 0
    else:
        result = result * 2
    finally:
        if result is None:
            result = -1
    return result
