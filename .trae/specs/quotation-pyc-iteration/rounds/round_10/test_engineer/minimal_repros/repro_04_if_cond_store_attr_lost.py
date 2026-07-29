"""R10 repro 04: STORE_ATTR in IfRegion condition block pre-stmts lost.

Pattern: if condition block contains `obj.attr = value` before the condition
test. The _if_extract_cond_instructions dropped STORE_ATTR.
"""
SOURCE = """
class C:
    pass

def f():
    obj = C()
    if obj:
        obj.name = 'x'
        if obj.name:
            return obj
    return None
"""

EXPECTED = SOURCE
