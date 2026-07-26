"""Repro 06-07: Orphan attribute expression (LOAD_ATTR without STORE).

Defect: `panel.items` (LOAD_ATTR without a following STORE/CALL/RETURN)
leaks as an orphan expression statement.

Root cause: orphan LOAD_ATTR Expr (a Name/Attribute reference with no
side effect) is not suppressed.
"""


def transform(panel):
    if fq == 'post':
        exrights_data = get_exrights()
        panel.items
        for stock in panel.items:
            data = change(stock, panel[stock])
            panel[stock] = data
    return panel
