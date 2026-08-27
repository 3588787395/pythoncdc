# Repro 03: with statement with multiple context managers
# Pattern: with A() as a, B() as b: ...
# Decompiler mishandles the nested context manager setup/teardown
def f(p1, p2):
    with open(p1) as f1, open(p2) as f2:
        return f1.read() + f2.read()
