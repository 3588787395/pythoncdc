"""R10 repro 03: STORE_SUBSCR in IfRegion condition block pre-stmts lost.

Pattern: if condition block contains `params[key] = value` before the condition
test. The _if_extract_cond_instructions only handled STORE_FAST/NAME/GLOBAL/DEREF,
dropping STORE_SUBSCR. Affects financial statement functions
(`params['page_no'] = str(page_no)`).
"""
SOURCE = """
def f(page_no):
    params = {}
    if params:
        params['page_no'] = str(page_no)
        if params['page_no']:
            return params
    return None
"""

EXPECTED = SOURCE
