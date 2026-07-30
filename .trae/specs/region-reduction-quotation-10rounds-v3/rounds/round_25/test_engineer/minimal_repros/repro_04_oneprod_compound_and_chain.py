"""Repro 04 - one_prod_to_dataframe: compound `and` condition in if/elif chain.

Original structure: `if i == 0 and len(v) == 8: ... elif i == 0 and len(v) == 10: ...`
(uniform compound conditions). CPython compiles each `i == 0` check to jump to the
NEXT elif (near target, no EXTENDED_ARG).

Observed decompiler behavior: splits the FIRST branch into `if i == 0: if len(v) == 8:`
(nested) while keeping the elifs compound. This makes the outer `if i == 0:` false-target
jump to the END (far, +EXTENDED_ARG) instead of the next elif. Semantically preserving
(elifs bind to the inner if) but produces +1 EXTENDED_ARG / +1 instruction.
"""
def f(i, v):
    index = []
    if i == 0 and len(v) == 8:
        index.append(v)
    elif i == 0 and len(v) == 10:
        index.append(v)
    elif i == 0 and len(v) == 12:
        index.append(v)
    elif i == 0 and len(v) == 14:
        index.append(v)
    return index
