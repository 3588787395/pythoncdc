# Repro 07: Nested function closing over outer variable (cell variable)
# Pattern: inner function references outer variable -> MAKE_CELL/LOAD_CLOSURE/STORE_DEREF
# Decompiler may lose COPY_FREE_VARS or mis-generate closure instructions
def make_adder(base):
    def add(x):
        return x + base
    return add
