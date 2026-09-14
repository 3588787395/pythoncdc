import sys, dis, marshal
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')

from pycdc import decompile_pyc

with open(r'F:\Downloads\pythoncdc-main\site-packages\IQEngine\data\merger_storage.pyc', 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

source = decompile_pyc(r'F:\Downloads\pythoncdc-main\site-packages\IQEngine\data\merger_storage.pyc')
decomp_code = compile(source, '<decompiled>', 'exec')

def find_code(code, name):
    if hasattr(code, 'co_name') and code.co_name == name: return code
    for c in getattr(code, 'co_consts', []):
        if hasattr(c, 'co_name'):
            r = find_code(c, name)
            if r: return r
    return None

orig_cls = find_code(orig_code, 'MergerStorage')
decomp_cls = find_code(decomp_code, 'MergerStorage')

orig_func = find_code(orig_cls, 'get_merger_date_info')
decomp_func = find_code(decomp_cls, 'get_merger_date_info')

orig_instrs = list(dis.get_instructions(orig_func))
decomp_instrs = list(dis.get_instructions(decomp_func))

print(f"Orig: {len(orig_instrs)}, Decomp: {len(decomp_instrs)}")
match = True
for i in range(min(len(orig_instrs), len(decomp_instrs))):
    oi = orig_instrs[i]
    di = decomp_instrs[i]
    if oi.opname != di.opname:
        print(f"DIFF at [{i}]: Orig={oi.opname} {oi.argval} | Decomp={di.opname} {di.argval}")
        match = False
        break
if match and len(orig_instrs) == len(decomp_instrs):
    print("MATCH!")
elif match:
    print(f"Length diff: Orig={len(orig_instrs)}, Decomp={len(decomp_instrs)}")
