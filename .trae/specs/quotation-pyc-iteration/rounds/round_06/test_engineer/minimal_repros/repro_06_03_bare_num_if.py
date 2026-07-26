"""Repro 06-03: Bare number as if condition (lost Compare).

Defect: `if e.code == 499:` becomes `if 499:` — the LOAD_FAST e +
LOAD_ATTR code + LOAD_CONST N + COMPARE_OP sequence that should form
the If condition is dropped, leaving only the bare constant.

Root cause: In _generate_try / handler body, a COMPARE_OP-based
condition preceding a conditional jump is not preserved as the If test.
"""


def handle(e):
    if e.code == 401:
        retry = 1
    elif e.code == 499:
        retry = 2
    else:
        retry = 0
    return retry
