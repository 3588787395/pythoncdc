"""Repro 07-02: D5 (P1) orphan Name Expr leak.

In `get_kline` the line `prod = data.get(prod_code)` is followed by
`prod` (a bare LOAD_FAST) which the decompiler emits as an orphan `Expr`
statement instead of suppressing it. Mirrors quotation.pyc line 247/251.

Expected defect:
    prod = data.get(prod_code)
    prod
    for item in prod:
        ...
"""


def get_kline(data, prod_code):
    fields = ['open', 'high', 'low']
    i = 0
    for item in fields:
        df[item] = []
        i = i + 1
    prod = data.get(prod_code)
    prod
    for item in prod:
        process(item)
    return result
