import dis, marshal
f = open('site-packages/IQEngine/utils/trade_schedule.pyc','rb')
f.read(16)
co = marshal.load(f)
print('co_names:', co.co_names)
print('co_consts (non-code):')
for i, c in enumerate(co.co_consts):
    if not hasattr(c, 'co_code'):
        if isinstance(c, frozenset):
            print(f'  [{i}] frozenset (len={len(c)})')
        else:
            print(f'  [{i}] {repr(c)}')
    else:
        print(f'  [{i}] <code {c.co_name}>')
print()
print('Number of code objects:', sum(1 for c in co.co_consts if hasattr(c, 'co_code')))
for c in co.co_consts:
    if hasattr(c, 'co_code'):
        print(f'  Function: {c.co_name}, args={c.co_argcount}, names={c.co_names}')
