import sys, marshal, types, dis
sys.path.insert(0, '.')
from testqouter.round1.base import compare_bytecode

pyc = 'site-packages/IQEngine/plugins/plugin_system_event_source/default_event_source.pyc'
ok = pyc.replace('.pyc', 'OK.py')
with open(pyc, 'rb') as f:
    f.read(16); orig = marshal.load(f)
import py_compile
cf = py_compile.compile(ok, doraise=True, quiet=2)
with open(cf, 'rb') as f:
    f.read(16); decomp = marshal.load(f)

def extract(co):
    r = {}; r[co.co_name] = co
    for c in co.co_consts:
        if isinstance(c, type(orig)): r.update(extract(c))
    return r

om = extract(orig); dm = extract(decomp)
co_o = om['events']; co_d = dm['events']
oi = list(dis.get_instructions(co_o)); di = list(dis.get_instructions(co_d))

# Find the first real instruction diff
for idx in range(min(len(oi), len(di))):
    if oi[idx].opname != di[idx].opname or oi[idx].arg != di[idx].arg:
        if oi[idx].opname not in ('EXTENDED_ARG',) and di[idx].opname not in ('EXTENDED_ARG',):
            if oi[idx].opname not in ('POP_JUMP_FORWARD_IF_FALSE','POP_JUMP_FORWARD_IF_TRUE','JUMP_FORWARD','JUMP_BACKWARD','FOR_ITER','JUMP_IF_FALSE_OR_POP','JUMP_IF_TRUE_OR_POP','POP_JUMP_FORWARD_IF_NOT_NONE','POP_JUMP_FORWARD_IF_NONE'):
                print(f'First real diff at idx {idx}: ORIG offset={oi[idx].offset} {oi[idx].opname}({oi[idx].arg}) DECOMP offset={di[idx].offset} {di[idx].opname}({di[idx].arg})')
                print(f'\nORIG around idx {idx}:')
                for i in oi[max(0,idx-5):idx+15]:
                    a = f'{i.arg} ({i.argrepr})' if i.arg is not None and i.argrepr else (str(i.arg) if i.arg is not None else '')
                    print(f'  {i.offset:4d} {i.opname:35s} {a}')
                print(f'\nDECOMP around idx {idx}:')
                for i in di[max(0,idx-5):idx+15]:
                    a = f'{i.arg} ({i.argrepr})' if i.arg is not None and i.argrepr else (str(i.arg) if i.arg is not None else '')
                    print(f'  {i.offset:4d} {i.opname:35s} {a}')
                break
