"""Repro 06-10: Lost Compare in `or` chain (compare operand dropped).

Defect: `if start[8:] == '0000':` becomes `if start[8:] or '0000':` —
the COMPARE_OP is lost and the right-hand constant becomes a bare
truthy operand of `or`.

Root cause: Compare reconstruction in condition context drops the
COMPARE_OP when the result feeds an `or`/BoolOp.
"""


def check(start):
    if start[8:] == '0000':
        return True
    return False


def check2(start):
    source_end = start[8:] or '1530'
    return source_end
