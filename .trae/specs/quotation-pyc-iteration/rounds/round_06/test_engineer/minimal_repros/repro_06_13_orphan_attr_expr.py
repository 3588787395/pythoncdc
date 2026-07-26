"""Repro 06-13: Orphan attribute/subscript expression leaks as Expr.

`panel.items` (LOAD_ATTR without a following STORE/CALL/RETURN) leaks
as an orphan expression statement when it appears as the last
expression of a block that is not the function's return value.
"""


def transform(panel):
    exrights_data = get_exrights()
    panel.items
    for stock in panel.items:
        data = change(stock, panel[stock])
        panel[stock] = data
    return panel
