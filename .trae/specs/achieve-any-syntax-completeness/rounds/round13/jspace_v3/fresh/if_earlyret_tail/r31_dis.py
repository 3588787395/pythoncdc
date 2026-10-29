import dis, types, sys
code = compile(open(r'D:\temp\opencode\r31_repro.py', encoding='utf-8').read(), 'r31_repro', 'exec')
for c in code.co_consts:
    if isinstance(c, types.CodeType) and c.co_name == 'f':
        print('=== f bytecode ===')
        dis.dis(c)
        break
