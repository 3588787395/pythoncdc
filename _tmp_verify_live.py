import marshal, types, dis, sys
from pycdc import decompile_pyc

pyc_file = 'site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc'

with open(pyc_file, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

src = decompile_pyc(pyc_file)
compiled = compile(src, '<decompiled>', 'exec')

def get_all_codes(code_obj, prefix=''):
    result = {prefix + code_obj.co_name: code_obj}
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            result.update(get_all_codes(const, prefix + code_obj.co_name + '.'))
    return result

orig_codes = get_all_codes(code, '')
new_codes = get_all_codes(compiled, '')

mismatches = 0
total = 0
for name, orig_co in sorted(orig_codes.items()):
    if name not in new_codes:
        print(f"MISSING: {name}")
        mismatches += 1
        continue
    new_co = new_codes[name]
    total += 1
    if (orig_co.co_code != new_co.co_code
            or orig_co.co_names != new_co.co_names
            or orig_co.co_varnames != new_co.co_varnames
            or orig_co.co_freevars != new_co.co_freevars
            or orig_co.co_cellvars != new_co.co_cellvars):
        mismatches += 1
        print(f"MISMATCH: {name}")
        orig_instrs = list(dis.get_instructions(orig_co))
        new_instrs = list(dis.get_instructions(new_co))
        for i, (o, n) in enumerate(zip(orig_instrs, new_instrs)):
            if o.opname != n.opname or o.arg != n.arg:
                print(f"  Instr {i}: orig={o.opname}({o.arg}) vs new={n.opname}({n.arg})")
        if len(orig_instrs) != len(new_instrs):
            print(f"  Length: orig={len(orig_instrs)} vs new={len(new_instrs)}")
            # Show tail
            print(f"  orig tail: {[(i.opname, i.arg) for i in orig_instrs[-5:]]}")
            print(f"  new tail:  {[(i.opname, i.arg) for i in new_instrs[-5:]]}")
    else:
        print(f"OK: {name}")

print(f"\n=== Summary: {total - mismatches}/{total} matched, {mismatches} mismatches ===")
