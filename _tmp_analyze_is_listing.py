"""Analyze is_listing bytecode mismatch in asset.pyc."""
import dis
import marshal
import types

pyc_path = "F:/Downloads/pythoncdc-main/site-packages/IQEngine/core/asset.pyc"
with open(pyc_path, 'rb') as f:
    f.read(4); f.read(4); f.read(8)
    orig_code = marshal.load(f)

ok_path = pyc_path.replace('.pyc', 'OK.py')
with open(ok_path, 'r', encoding='utf-8') as f:
    source = f.read()
decomp_code = compile(source, ok_path, 'exec')

def find_all_codes(code_obj, name, results=None):
    if results is None:
        results = []
    if code_obj.co_name == name:
        results.append(code_obj)
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            find_all_codes(const, name, results)
    return results

orig_listings = find_all_codes(orig_code, 'is_listing')
decomp_listings = find_all_codes(decomp_code, 'is_listing')

NOISE = {'RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'EXTENDED_ARG', 'PRECALL', 'COPY_FREE_VARS', 'MAKE_CELL'}

def get_filtered(code_obj):
    return [(i.offset, i.opname, i.arg, i.argrepr) 
            for i in dis.get_instructions(code_obj)
            if i.opname not in NOISE]

# Compare all is_listing implementations
for idx, (orig_co, decomp_co) in enumerate(zip(orig_listings, decomp_listings)):
    orig_instrs = get_filtered(orig_co)
    decomp_instrs = get_filtered(decomp_co)
    
    # Only show the one that mismatches
    if orig_instrs == decomp_instrs:
        continue
    
    print(f"is_listing #{idx}: orig={len(orig_instrs)} decomp={len(decomp_instrs)} instrs")
    print(f"  ORIG:")
    for i, (offset, opname, arg, argrepr) in enumerate(orig_instrs):
        print(f"    [{i:2d}] {offset:4d}  {opname:<30} {argrepr}")
    print(f"  DECOMP:")
    for i, (offset, opname, arg, argrepr) in enumerate(decomp_instrs):
        print(f"    [{i:2d}] {offset:4d}  {opname:<30} {argrepr}")
    print()
