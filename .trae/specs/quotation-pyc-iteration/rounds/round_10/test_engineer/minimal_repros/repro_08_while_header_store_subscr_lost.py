"""R10 repro 08: STORE_SUBSCR in while loop header block lost.

Pattern: while loop header block contains `params[key] = value` before the
condition test. The _loop_process_header_instructions dropped STORE_SUBSCR.
Affects growth_ability etc. (`params['page_no'] = str(page_no)`).
"""
SOURCE = """
def f(page_no):
    params = {}
    while True:
        params['page_no'] = str(page_no)
        if params['page_no']:
            break
        page_no += 1
    return params
"""

EXPECTED = SOURCE
