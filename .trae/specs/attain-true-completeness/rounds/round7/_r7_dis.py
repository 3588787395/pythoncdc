# -*- coding: utf-8 -*-
"""R7 probe: dis a function (by name, recursive) from a pyc."""
import dis
import marshal
import sys
import types

path = sys.argv[1]
fname = sys.argv[2]

with open(path, 'rb') as f:
    code = marshal.loads(f.read()[16:])


def find(co):
    if co.co_name == fname:
        return co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r = find(c)
            if r is not None:
                return r
    return None


t = find(code)
if t is None:
    print('NOT FOUND')
    sys.exit(1)
print('=== %s varnames=%s ===' % (t.co_name, t.co_varnames))
for i in dis.get_instructions(t):
    print('%5s %-28s %s' % (i.offset, i.opname, i.argrepr))
print('--- exception table ---')
for e in dis._parse_exception_table(t):
    print(e)
