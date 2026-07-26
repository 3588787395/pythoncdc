"""Repro 08-09: D8 variant — nested if/elif/else + return in branches.

A function body where the if/elif/else branches each return a value
computed from locals. The decompiler may collapse the entire body
into a single bare Expr (D8 pattern).

Expected defect: the function body is collapsed into a single
`int(...)` or similar bare Expr wrapping an IfExp; the local
assignments and return statements are lost.
"""


def date_convert(date, report_types):
    if report_types is None:
        if date[5:7] == '01':
            return date[:4] + '-12-31'
        else:
            return date[:4] + '-03-31'
    else:
        if int(date[5:7]) <= report_types:
            return date[:4] + '-12-31'
        else:
            return date[:4] + '-03-31'
