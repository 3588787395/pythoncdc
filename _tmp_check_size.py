import dis
code = compile('x = 1', '<test>', 'exec')
instrs = list(dis.get_instructions(code))
for i in instrs:
    has_size = hasattr(i, 'size')
    print(f'{i.opname}: offset={i.offset}, has_size={has_size}, arg={i.arg}')
