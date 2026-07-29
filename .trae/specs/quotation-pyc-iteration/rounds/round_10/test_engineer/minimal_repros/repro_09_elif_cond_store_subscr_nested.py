"""R10 repro 09: STORE_SUBSCR in elif condition with nested if.

Pattern: elif condition block contains `dict[key] = value` (STORE_SUBSCR)
before the condition test, followed by a nested if. The STORE_SUBSCR was
dropped by _if_extract_cond_instructions.
"""
SOURCE = """
def f(fields, date):
    params = {}
    if not fields:
        return None
    params['fields'] = fields
    if date:
        return params
    return -1
"""

EXPECTED = SOURCE
