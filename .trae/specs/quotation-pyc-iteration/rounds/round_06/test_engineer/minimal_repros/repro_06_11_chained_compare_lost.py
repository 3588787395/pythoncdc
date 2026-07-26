"""Repro 06-11: Lost chained comparison (becomes bare number).

Defect: `if 400 <= e.code <= 499:` (chained comparison) is reduced to
`if 499:` — the LOAD_CONST lo + LOAD_FAST + LOAD_ATTR + SWAP/COPY +
COMPARE_OP chain that builds the chained comparison is dropped, leaving
only the final LOAD_CONST hi as the if-test.
"""


def classify(e):
    if 400 <= e.code <= 499:
        return 'client_error'
    if 500 <= e.code <= 599:
        return 'server_error'
    return 'other'
