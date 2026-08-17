"""Analyze create_trade bytecode."""
import dis
import marshal
import types

pyc_path = "F:/Downloads/pythoncdc-main/site-packages/IQEngine/account/trade.pyc"
with open(pyc_path, 'rb') as f:
    f.read(4); f.read(4); f.read(8)
    code = marshal.load(f)

ok_path = pyc_path.replace('.pyc', 'OK.py')
with open(ok_path, 'r', encoding='utf-8') as f:
    source = f.read()
decomp_code = compile(source, ok_path, 'exec')

def find_code(code_obj, name):
    if code_obj.co_name == name:
        return code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            result = find_code(const, name)
            if result:
                return result
    return None

target = 'create_trade'
orig_co = find_code(code, target)
decomp_co = find_code(decomp_code, target)

NOISE = {'RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'EXTENDED_ARG', 'PRECALL', 'COPY_FREE_VARS', 'MAKE_CELL'}

def get_filtered(code_obj):
    return [(i.offset, i.opname, i.arg, i.argrepr) 
            for i in dis.get_instructions(code_obj)
            if i.opname not in NOISE]

orig_instrs = get_filtered(orig_co)
decomp_instrs = get_filtered(decomp_co)

print(f"Original: {len(orig_instrs)} filtered instructions")
print(f"Decompiled: {len(decomp_instrs)} filtered instructions")

print(f"\n{'ORIG':<50} {'DECOMP':<50}")
for i in range(max(len(orig_instrs), len(decomp_instrs))):
    o = orig_instrs[i] if i < len(orig_instrs) else (0, '---', 0, '')
    d = decomp_instrs[i] if i < len(decomp_instrs) else (0, '---', 0, '')
    o_str = f"{o[1]} {o[3]}" if o[1] != '---' else '---'
    d_str = f"{d[1]} {d[3]}" if d[1] != '---' else '---'
    print(f"  {i:3d}  {o_str:<50} {d_str:<50}")
