"""R21: dump dec _target"""
import dis, types

def collect(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, out)
    return out

dec_src = open(r'f:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/handlersOK.py', 'r', encoding='utf-8').read()
compiled = compile(dec_src, '<decompiled>', 'exec')

dec_targets = [c for c in collect(compiled, []) if c.co_name == '_target']
dec = dec_targets[-1]

print(f'== dec _target varnames={dec.co_varnames} ==')
for i in dis.get_instructions(dec):
    if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'EXTENDED_ARG'):
        print(f'{i.offset:4d}: {i.opname:40s} {i.argval}')
