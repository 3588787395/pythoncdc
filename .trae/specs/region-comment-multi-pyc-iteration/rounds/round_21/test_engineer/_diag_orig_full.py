"""R21: dump orig _target instructions"""
import marshal, sys, types, dis
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')

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

root = load_pyc(r'f:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/handlers.pyc')
targets = [c for c in collect(root, []) if c.co_name == '_target']
orig = targets[-1]

print(f'== orig _target varnames={orig.co_varnames} ==')
for i in dis.get_instructions(orig):
    if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'EXTENDED_ARG'):
        print(f'{i.offset:4d}: {i.opname:40s} {i.argval}')
