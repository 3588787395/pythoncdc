import sys, types, dis
sys.path.insert(0, '/workspace')
from core.pyc_loader_v2 import load_pyc_file_v2

def get_instr_list(co):
    out = []
    for ins in dis.get_instructions(co):
        if ins.opname == 'CACHE':
            continue
        av = ins.argval
        if isinstance(av, types.CodeType):
            out.append(('CODE', av.co_name, get_instr_list(av)))
        else:
            out.append((ins.opname, av))
    return out

module = load_pyc_file_v2('/workspace/quotation.pyc')
co = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(co, 'to_python_code'):
    co = co.to_python_code()
orig = get_instr_list(co)

with open('/tmp/r25_decompiled.py') as f:
    src = f.read()
new = get_instr_list(compile(src, '<d>', 'exec'))

# find build_future_fill_time
def find(il, name):
    for item in il:
        if item[0] == 'CODE' and item[1] == name:
            return item[2]
    return None

oa = find(orig, 'build_future_fill_time')
na = find(new, 'build_future_fill_time')
print(f"orig len={len(oa)} new len={len(na)}")
n = min(len(oa), len(na))
diffs = []
for i in range(n):
    if oa[i] != na[i]:
        diffs.append(i)
print(f"diff count={len(diffs)}")
for i in diffs[:40]:
    print(f"  idx{i}: ORIG={oa[i]} | NEW={na[i]}")
