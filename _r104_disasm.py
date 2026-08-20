import dis, marshal, struct, sys

path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_09_multi_elif_break.pyc'
with open(path, 'rb') as f:
    magic = f.read(4)
    flags = struct.unpack('<I', f.read(4))[0]
    f.read(8)
    code = marshal.load(f)

# Print all code objects
def print_code(c, indent=0):
    prefix = '  ' * indent
    print(f'{prefix}Code: {c.co_name} (argcount={c.co_argcount})')
    print(f'{prefix}  consts: {c.co_consts}')
    print(f'{prefix}  names: {c.co_names}')
    print(f'{prefix}  varnames: {c.co_varnames}')
    print(f'{prefix}  Bytecode:')
    for instr in dis.get_instructions(c):
        print(f'{prefix}    {instr.offset:4d} {instr.opname:30s} {instr.arg if instr.arg is not None else ""} {instr.argrepr}')
    # Exception table
    if hasattr(c, 'co_exceptiontable'):
        print(f'{prefix}  Exception table:')
        try:
            from dis import parse_exception_table
            for entry in parse_exception_table(c):
                print(f'{prefix}    {entry}')
        except Exception as e:
            print(f'{prefix}    (parse error: {e})')
    for const in c.co_consts:
        if hasattr(const, 'co_code'):
            print_code(const, indent+1)

print_code(code)
