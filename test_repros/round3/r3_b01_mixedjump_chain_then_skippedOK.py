# Source Generated with Decompyle++ (Python version)
# File: r3_b01_mixedjump_chain_then_skipped.pyc (Python 3.11)

def f(fq, div, fields):
    if fq is not None and div:
        if isinstance(fields, str) and 'x' in fields:
            need = 0
        else:
            need = 1
    for t in TYPES:
        use(need, t)
    return need
