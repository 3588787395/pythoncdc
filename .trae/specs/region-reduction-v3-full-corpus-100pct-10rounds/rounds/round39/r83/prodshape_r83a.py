"""Compile a product module whole; dump resolved jump targets + co_lines mapping for one unit."""
import dis, marshal, os, sys, types

prod = sys.argv[1]
pyc = sys.argv[2]
unit = sys.argv[3]
LO, HI = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (0, 10**9)

src = open(prod, encoding='utf-8').read()
mod = compile(src, os.path.basename(prod), 'exec')
orig = marshal.loads(open(pyc, 'rb').read()[16:])


def find(c, name, acc=None):
    for x in c.co_consts:
        if isinstance(x, type(c)) and x.co_name == name:
            return x
        if isinstance(x, type(c)):
            r = find(x, name)
            if r:
                return r


def gather(c, acc):
    acc.append(c)
    for cst in c.co_consts:
        if isinstance(cst, type(c)):
            gather(cst, acc)


co_p = find(mod, unit)
co_o = find(orig, unit)
print('prod co_code len=%d  orig co_code len=%d' % (len(co_p.co_code), len(co_o.co_code)))
lm = {}
for s, e, l in co_p.co_lines():
    for o in range(s, e):
        lm[o] = l
print('--- prod jumps in [%d,%d]' % (LO, HI))
for i in dis.get_instructions(co_p):
    if LO <= i.offset <= HI and (i.opname.startswith('JUMP') or 'BRANCH' in i.opname or i.opname.startswith('POP_JUMP')):
        print('@%-6d %-30s -> %-6s line=%s' % (i.offset, i.opname, i.argrepr, lm.get(i.offset)))
print('--- prod line map for instructions near the windows')
for i in dis.get_instructions(co_p):
    if LO <= i.offset <= HI:
        print('@%-6d %-30s %-22s line=%s' % (i.offset, i.opname, (i.argrepr or '')[:22], lm.get(i.offset)))
