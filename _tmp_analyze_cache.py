"""Analyze func_wrapper bytecode mismatch in cache_storage.pyc."""
import dis, marshal, types

pyc = "F:/Downloads/pythoncdc-main/site-packages/IQEngine/utils/cache_storage.pyc"
with open(pyc, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

ok = pyc.replace('.pyc', 'OK.py')
with open(ok, 'r', encoding='utf-8') as f:
    source = f.read()
decomp_code = compile(source, ok, 'exec')

def find_code(code_obj, name, results=None):
    if results is None: results = []
    if code_obj.co_name == name: results.append(code_obj)
    for c in code_obj.co_consts:
        if isinstance(c, types.CodeType): find_code(c, name, results)
    return results

# Find func_wrapper in both
orig_fws = find_code(code, 'func_wrapper')
decomp_fws = find_code(decomp_code, 'func_wrapper')

# They might be nested, find the right one
for orig_co, decomp_co in zip(orig_fws, decomp_fws):
    NOISE = {'RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'EXTENDED_ARG', 'PRECALL', 'COPY_FREE_VARS', 'MAKE_CELL'}
    orig_instrs = [(i.offset, i.opname, i.arg, i.argrepr) for i in dis.get_instructions(orig_co) if i.opname not in NOISE]
    decomp_instrs = [(i.offset, i.opname, i.arg, i.argrepr) for i in dis.get_instructions(decomp_co) if i.opname not in NOISE]
    
    if orig_instrs == decomp_instrs:
        continue
    
    print(f"func_wrapper: orig={len(orig_instrs)} decomp={len(decomp_instrs)} instrs")
    
    # Find diffs
    for i in range(max(len(orig_instrs), len(decomp_instrs))):
        o = orig_instrs[i] if i < len(orig_instrs) else (0, '---', 0, '')
        d = decomp_instrs[i] if i < len(decomp_instrs) else (0, '---', 0, '')
        if o[1] != d[1] or o[3] != d[3]:
            print(f"  DIFF [{i:3d}]: ORIG={o[1]:<25} {o[3]:<30} | DECOMP={d[1]:<25} {d[3]}")
            # Show context
            for j in range(max(0, i-3), min(max(len(orig_instrs), len(decomp_instrs)), i+4)):
                o2 = orig_instrs[j] if j < len(orig_instrs) else (0, '---', 0, '')
                d2 = decomp_instrs[j] if j < len(decomp_instrs) else (0, '---', 0, '')
                marker = '>>' if j == i else '  '
                print(f"  {marker}[{j:3d}]  {o2[1]:<25} {str(o2[3]):<30} | {d2[1]:<25} {d2[3]}")
            print()
    break
