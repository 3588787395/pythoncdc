"""R10 repro 07: STORE_SUBSCR in entry block before while loop.

Pattern: function entry block contains `params[key] = value` before a while
loop. The entry block pre-stmts extraction dropped STORE_SUBSCR, causing
the assignment to be lost before the loop header.
"""
SOURCE = """
def f(page_no):
    params = {}
    params['page_no'] = str(page_no)
    while params['page_no']:
        params['page_no'] = None
    return params
"""

EXPECTED = SOURCE
