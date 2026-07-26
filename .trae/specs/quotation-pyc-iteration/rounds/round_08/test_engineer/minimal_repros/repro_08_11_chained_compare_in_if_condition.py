"""Repro 08-11 (bonus): D3 in if condition (not inside except handler).

The D3 defect in `api_get_financial` fires inside an `except HTTPError`
handler. The chained compare `400 <= e.code <= 499` is also commonly
used outside except handlers. This repro checks whether the D3 defect
also reproduces when the chained compare is in a plain `if` (not in
an except handler).

Expected defect: `if 499:` (chained compare lost). If the chained
compare survives in isolation, this repro is NOT-REPRO (the
defect depends on the surrounding except-handler CFG).
"""


def classify(code):
    if 400 <= code <= 499:
        return 'client_error'
    elif 500 <= code <= 599:
        return 'server_error'
    else:
        return 'other'
