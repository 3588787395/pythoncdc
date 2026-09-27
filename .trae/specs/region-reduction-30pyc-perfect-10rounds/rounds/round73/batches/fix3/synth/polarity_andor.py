# -*- coding: utf-8 -*-
"""R73 F-POLARITY minimal repro (and/or mixed short-circuit chain).

Trigger: the chain head is an `and` group whose false exit skips to the next
`or` operand, so the candidate then-entry block handed to the or-chain walk is
still a condition segment (not the then body).  Controls are shapes that must
keep byte-identical output (plain or, R13c `not A or B`, nested if body,
`and` group without `not`).
"""


def trig_mixed_or(A, B, C):
    if (A and not B) or C:
        return 1
    return 2


def trig_mixed_or_body(A, B, C):
    if (A and not B) or C:
        x = 1
        return x
    return 2


def ctrl_plain_or(A, B):
    if A or B:
        return 1
    return 2


def ctrl_not_or(A, B):
    if not A or B:
        return 1
    return 2


def ctrl_nested_body(A, B, C):
    if A or B:
        if C:
            return 1
        return 3
    return 2


def ctrl_and_group(A, B, C):
    if (A and B) or C:
        return 1
    return 2
