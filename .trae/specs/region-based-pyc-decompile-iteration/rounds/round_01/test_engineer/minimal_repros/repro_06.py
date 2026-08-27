# Repro 06: frozenset literal used in membership test
# Pattern: frozenset({...}) constant used with 'in' operator
# Decompiler may represent frozenset constant as tuple
_VALID = frozenset({'a', 'b', 'c'})

def check(x):
    return x in _VALID
