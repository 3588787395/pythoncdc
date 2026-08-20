import ast, dis, marshal

# Original
f = open('decompiler_test_comprehensive.cpython-311.pyc', 'rb')
f.read(16)
code = marshal.load(f)
dp = [c for c in code.co_consts if hasattr(c, 'co_name') and c.co_name == 'DataProcessor'][0]
vd = [c for c in dp.co_consts if hasattr(c, 'co_name') and c.co_name == 'validate_data'][0]

# Decompiled
f2 = open('_r108_out4.py', 'r', encoding='utf-8', errors='replace')
src = f2.read()
tree = ast.parse(src)
cls = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == 'DataProcessor'][0]
mod = ast.Module(body=[ast.ClassDef(name='DP', bases=[], keywords=[], body=cls.body, decorator_list=[])], type_ignores=[])
mod2 = ast.fix_missing_locations(mod)
comp = compile(mod2, '<x>', 'exec')
dp2 = [c for c in comp.co_consts if hasattr(c, 'co_name') and c.co_name == 'validate_data'][0]

orig_instrs = [(i.offset, i.opname, i.argval, i.argrepr) for i in dis.get_instructions(vd)]
decomp_instrs = [(i.offset, i.opname, i.argval, i.argrepr) for i in dis.get_instructions(dp2)]

print(f"Orig: {len(orig_instrs)} instrs, Decomp: {len(decomp_instrs)} instrs")
print()

# Find first difference
max_len = max(len(orig_instrs), len(decomp_instrs))
diffs = []
for i in range(max_len):
    o = orig_instrs[i] if i < len(orig_instrs) else None
    d = decomp_instrs[i] if i < len(decomp_instrs) else None
    if o != d:
        diffs.append((i, o, d))

print(f"Total diffs: {len(diffs)}")
print()
for idx, o, d in diffs[:30]:
    print(f"  [{idx}] orig={o}")
    print(f"        decomp={d}")
    print()
