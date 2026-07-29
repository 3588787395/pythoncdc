"""R10 repro 01: STORE_SUBSCR in entry block pre-stmts lost.

Pattern: function entry block contains `dict[key] = value` before a loop/if.
The entry block pre-stmts extraction only handled STORE_FAST/NAME/GLOBAL/DEREF,
dropping STORE_SUBSCR. Affects balance_statement etc. (`return_data['data'] = []`).
"""
SOURCE = """
def f():
    return_data = {}
    return_data['data'] = []
    return_data['error'] = 'ok'
    return return_data
"""

EXPECTED = SOURCE
