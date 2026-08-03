"""R21: semantic comparison ignoring jump targets"""
import marshal, sys, types, dis

def load_pyc(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def collect(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, out)
    return out

def normalize(code_obj):
    instrs = []
    for i in dis.get_instructions(code_obj):
        if i.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'EXTENDED_ARG'):
            continue
        # For jump instructions, only keep opname (not target offset)
        if i.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                        'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                        'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'):
            instrs.append((i.opname, '<jump>'))
        else:
            instrs.append((i.opname, i.argval))
    return instrs

root = load_pyc(r'f:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/handlers.pyc')
targets = [c for c in collect(root, []) if c.co_name == '_target']
orig = targets[-1]

with open(r'f:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/handlersOK.py', 'r', encoding='utf-8') as f:
    dec_src = f.read()
compiled = compile(dec_src, '<decompiled>', 'exec')
dec_targets = [c for c in collect(compiled, []) if c.co_name == '_target']
dec = dec_targets[-1]

orig_n = normalize(orig)
dec_n = normalize(dec)

print(f'orig: {len(orig_n)} instrs (normalized)')
print(f'dec:  {len(dec_n)} instrs (normalized)')

diffs = 0
for oi, di in zip(orig_n, dec_n):
    if oi != di:
        print(f'  DIFF: orig={oi} dec={di}')
        diffs += 1

if len(orig_n) != len(dec_n):
    print(f'  Length mismatch: orig={len(orig_n)} dec={len(dec_n)}')

print(f'\nTotal semantic differences (ignoring jump targets): {diffs}')
