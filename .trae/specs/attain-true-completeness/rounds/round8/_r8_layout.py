# -*- coding: utf-8 -*-
"""R8 probe: compile small try/except/else/finally layouts and show offsets."""
import dis
import sys

CASES = {
    'try_except_else': """
def f():
    try:
        x = 1
    except ValueError:
        x = 2
    else:
        x = 3
""",
    'try_except_else_finally': """
def f():
    try:
        x = 1
    except ValueError:
        x = 2
    else:
        x = 3
    finally:
        x = 4
""",
    'try_finally': """
def f():
    try:
        x = 1
    finally:
        x = 4
""",
    'nested_inner_try_except_finally': """
def f():
    try:
        try:
            x = 1
        except ValueError:
            x = 2
        finally:
            x = 3
    except NameError:
        x = 4
    else:
        x = 5
    finally:
        x = 6
""",
    'nested_inner_try_except_only': """
def f():
    try:
        try:
            x = 1
        except ValueError:
            x = 2
    except NameError:
        x = 4
    else:
        x = 5
""",
}

for name, src in CASES.items():
    co = compile(src, name, 'exec')
    for c in co.co_consts:
        if hasattr(c, 'co_code'):
            co = c
            break
    print('=== %s ===' % name)
    for i in dis.get_instructions(co):
        print('%5s %-28s %s' % (i.offset, i.opname, i.argrepr))
    for e in dis._parse_exception_table(co):
        print('   EXC', e)
    print()
