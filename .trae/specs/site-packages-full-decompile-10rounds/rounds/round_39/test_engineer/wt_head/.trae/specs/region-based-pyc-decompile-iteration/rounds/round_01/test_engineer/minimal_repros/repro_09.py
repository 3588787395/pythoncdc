# Repro 09: try/except with bare raise (re-raise) and multiple except clauses
# Pattern: except with bare 'raise' (RERAISE) followed by another except
# Decompiler may produce wrong POP_EXCEPT/COPY/RERAISE ordering
def process(data):
    try:
        if data is None:
            raise ValueError("null")
        return len(data)
    except ValueError:
        raise
    except TypeError:
        return 0
