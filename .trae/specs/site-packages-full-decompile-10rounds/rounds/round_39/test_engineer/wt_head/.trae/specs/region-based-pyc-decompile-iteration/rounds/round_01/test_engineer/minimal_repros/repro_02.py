# Repro 02: Nested try/except with return in inner handler
# Pattern: try inside try, inner has return, outer has different exception
# Decompiler misstructures the POP_EXCEPT/RERAISE/COPY sequence
def f(x):
    try:
        try:
            return int(x)
        except ValueError:
            return 0
    except Exception:
        return -1
