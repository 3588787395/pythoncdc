"""R21: detailed bytecode diff for handlers.pyc _target"""
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

def normalize(code_obj):
    instrs = []
    for i in dis.get_instructions(code_obj):
        if i.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'EXTENDED_ARG'):
            continue
        instrs.append((i.offset, i.opname, i.argval))
    return instrs

root = load_pyc(r'f:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/handlers.pyc')
targets = [c for c in collect(root, []) if c.co_name == '_target']
orig = targets[-1]

# Compile decompiled source
with open(r'f:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/handlersOK.py', 'r', encoding='utf-8') as f:
    dec_src = f.read()
compiled = compile(dec_src, '<decompiled>', 'exec')
dec_targets = [c for c in collect(compiled, []) if c.co_name == '_target']
dec = dec_targets[-1]

orig_instrs = normalize(orig)
dec_instrs = normalize(dec)

print(f'orig: {len(orig_instrs)} instrs')
print(f'dec:  {len(dec_instrs)} instrs')

# Show first 30 differences
diff_count = 0
oi, di = 0, 0
while oi < len(orig_instrs) and di < len(dec_instrs):
    if orig_instrs[oi] != dec_instrs[di]:
        if diff_count < 30:
            print(f'  DIFF @{oi}/{di}: orig={orig_instrs[oi]} dec={dec_instrs[di]}')
        diff_count += 1
        # Try to resync
        oi += 1
        di += 1
    else:
        oi += 1
        di += 1

# Remaining
if oi < len(orig_instrs):
    print(f'  ORIG extra ({len(orig_instrs)-oi}):')
    while oi < len(orig_instrs) and diff_count < 30:
        print(f'    {orig_instrs[oi]}')
        oi += 1
        diff_count += 1
if di < len(dec_instrs):
    print(f'  DEC extra ({len(dec_instrs)-di}):')
    while di < len(dec_instrs) and diff_count < 30:
        print(f'    {dec_instrs[di]}')
        di += 1
        diff_count += 1

print(f'\nTotal differences: {diff_count}')
