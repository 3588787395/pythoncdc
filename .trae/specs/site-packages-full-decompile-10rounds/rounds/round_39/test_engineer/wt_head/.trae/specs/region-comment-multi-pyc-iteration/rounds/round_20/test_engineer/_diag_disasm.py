"""R20 diag: disasm logger/__init__.pyc user_print + <module> first_diff region."""
import dis
import marshal
import sys

PYC = r'F:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/__init__.pyc'

with open(PYC, 'rb') as f:
    f.read(16)
    code = marshal.load(f)


def find_co(c, name):
    if c.co_name == name:
        return c
    for k in c.co_consts:
        if hasattr(k, 'co_code'):
            r = find_co(k, name)
            if r is not None:
                return r
    return None


print('=== <module> first 80 instructions ===')
for i, ins in enumerate(dis.get_instructions(code)):
    if i >= 80:
        break
    print(f'{ins.offset:4d} {ins.opname:30s} {ins.argrepr}')


print('\n=== user_print co_consts ===')
up = find_co(code, 'user_print')
if up is None:
    print('NOT FOUND')
    sys.exit(0)
print('co_varnames:', up.co_varnames)
print('co_argcount:', up.co_argcount)
print('co_posonlyargcount:', up.co_posonlyargcount)
print('co_kwonlyargcount:', up.co_kwonlyargcount)
print('co_flags:', hex(up.co_flags))
print('co_consts:', up.co_consts)
print('co_names:', up.co_names)
print('co_freevars:', up.co_freevars)
print('co_cellvars:', up.co_cellvars)
print('\n=== user_print full disasm ===')
dis.dis(up)

print('\n=== <module> consts (with code objects marked) ===')
for i, c in enumerate(code.co_consts):
    if hasattr(c, 'co_code'):
        print(f'  [{i}] <code {c.co_name}>')
    else:
        print(f'  [{i}] {c!r}')
