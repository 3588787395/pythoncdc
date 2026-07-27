"""R10 repro 05: elif condition block pre-stmts lost.

Pattern: elif condition block contains an assignment before the condition test.
The _if_generate_elif_chain manual instruction loop cleared elif_cond_instrs on
STORE_FAST, dropping the assignment. Affects get_growth_ability etc.
(`fields = re_fields`).
"""
SOURCE = """
def f(fields):
    error_re, re_fields = divmod(len(fields), 2)
    if error_re != 0:
        return None
    fields = re_fields
    if fields > 0:
        return fields
    return -1
"""

EXPECTED = SOURCE
