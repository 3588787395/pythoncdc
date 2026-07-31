"""R14 CTRL 10: simple if/elif/else with str.replace (endswith_transe_2to4).

CTRL (NO-DEFECT): mirrors tools.pyc endswith_transe_2to4 — a flat
if/elif/else chain with str.replace calls and no nesting. This is one of the
5/6 already-matching functions in tools.pyc and serves as a control group
for the if/elif/else structure without the nested-if-in-else complication.
"""


def endswith_transe_2to4(code):
    if code.endswith('SS'):
        code = code.replace('SS', 'XSHG')
    elif code.endswith('SZ'):
        code = code.replace('SZ', 'XSHE')
    else:
        code = code
    return code
