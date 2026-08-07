import dis, marshal
f = open('site-packages/IQEngine/utils/trade_schedule.pyc','rb')
f.read(16)
co = marshal.load(f)
# Print bytecode for each function
for c in co.co_consts:
    if hasattr(c, 'co_code'):
        print(f'\n=== Function: {c.co_name} ===')
        print(f'  args={c.co_argcount}, varnames={c.co_varnames}')
        print(f'  names={c.co_names}')
        print(f'  consts (non-code):')
        for i, k in enumerate(c.co_consts):
            if not hasattr(k, 'co_code'):
                print(f'    [{i}] {repr(k)}')
            else:
                print(f'    [{i}] <code {k.co_name}>')
        print(f'  freevars={c.co_freevars}, cellvars={c.co_cellvars}')
        dis.dis(c)
        print()
