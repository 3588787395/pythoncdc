# -*- coding: utf-8 -*-
"""Disassemble every nested code object under a named function (orig pyc or compiled product)."""
import dis, io, marshal, sys, types
sys.stdout.reconfigure(encoding='utf-8')
path, name, prod = sys.argv[1], sys.argv[2], (len(sys.argv)>3 and sys.argv[3]=='--prod')
def walk(c,o):
    o.append(c)
    for k in c.co_consts:
        if isinstance(k, types.CodeType): walk(k,o)
    return o
if prod:
    root = compile(io.open(path, encoding='utf-8').read(), path, 'exec')
else:
    d = io.open(path,'rb').read()
    root = marshal.loads(d[16:])
alls = walk(root, [])
# find the target function code object
tgt = [c for c in alls if c.co_name == name]
print('found %d code objects named %s' % (len(tgt), name))
for t in tgt:
    print('=== %s varnames=%s freevars=%s ===' % (t.co_name, t.co_varnames, t.co_freevars))
    nested = walk(t, [])[1:] if False else None
    def sub(c, depth=1):
        for k in c.co_consts:
            if isinstance(k, types.CodeType):
                print('--- %s%s varnames=%s freevars=%s nconsts=%d' % ('  '*depth, k.co_name, k.co_varnames, k.co_freevars, len(k.co_consts)))
                for i in dis.get_instructions(k):
                    if i.opname != 'CACHE':
                        print('      %5d %-26s %s' % (i.offset, i.opname, str(i.argrepr)[:60]))
                sub(k, depth+1)
    sub(t)
