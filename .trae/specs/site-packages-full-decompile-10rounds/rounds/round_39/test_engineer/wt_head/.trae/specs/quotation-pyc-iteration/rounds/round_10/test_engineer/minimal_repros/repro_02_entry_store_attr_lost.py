"""R10 repro 02: STORE_ATTR in entry block pre-stmts lost.

Pattern: function entry block contains `obj.attr = value` before a loop/if.
The entry block pre-stmts extraction only handled STORE_FAST/NAME/GLOBAL/DEREF,
dropping STORE_ATTR.
"""
SOURCE = """
class C:
    pass

def f():
    obj = C()
    obj.name = 'x'
    obj.value = 42
    return obj
"""

EXPECTED = SOURCE
