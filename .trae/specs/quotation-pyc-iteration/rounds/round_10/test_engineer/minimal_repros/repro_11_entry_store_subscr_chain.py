"""R10 repro 11: STORE_SUBSCR chain in entry block before if.

Pattern: multiple STORE_SUBSCR assignments in the entry block before an if
statement. All must be preserved as independent pre-stmts.
"""
SOURCE = """
def f():
    d = {}
    d['a'] = 1
    d['b'] = 2
    d['c'] = 3
    if d['a']:
        return d
    return None
"""

EXPECTED = SOURCE
