import dis
import io
import sys

base = '.trae/specs/attack-completeness-claims/rounds/round4/'

for p in ['_probes/cp_except_tuple_orderOK.py', '_scratch/construct/cp_except_tuple_order_mut.py']:
    src = io.open(base + p, encoding='utf-8').read()
    c = compile(src, 'x', 'exec')
    print('===', p)
    for k in c.co_consts:
        if hasattr(k, 'co_code'):
            print('  -- %s --' % k.co_name)
            for i in dis.get_instructions(k):
                print('    %-22s arg=%-4s argval=%r' % (i.opname, i.arg, i.argval))
    print('  module exceptiontable:', c.co_exceptiontable)
