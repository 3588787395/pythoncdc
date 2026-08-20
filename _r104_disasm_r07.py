import dis, marshal, struct

path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_07_finally_implicit_return.pyc'
with open(path, 'rb') as f:
    f.read(4); f.read(4); f.read(8)
    code = marshal.load(f)

func_code = code.co_consts[1]
print(f'Function: {func_code.co_name}')
print(f'consts: {func_code.co_consts}')
print(f'\nBytecode:')
for instr in dis.get_instructions(func_code):
    print(f'  {instr.offset:4d} {instr.opname:30s} {instr.arg if instr.arg is not None else ""} {instr.argrepr}')
