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

cls = None
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef) and node.name == 'DataProcessor':
        cls = node
        break

new_cls = ast.ClassDef(name='DP', bases=[], keywords=[], body=cls.body, decorator_list=[])
mod = ast.Module(body=[new_cls], type_ignores=[])
mod = ast.fix_missing_locations(mod)
comp = compile(mod, '<x>', 'exec')

# validate_data is nested inside DP class code
dp2 = None
for c in comp.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'DP':
        for cc in c.co_consts:
            if hasattr(cc, 'co_name') and cc.co_name == 'validate_data':
                dp2 = cc
                break
    if dp2:
        break

if dp2 is None:
    print("ERROR: validate_data not found")
    exit(1)

orig_instrs = [(i.offset, i.opname, i.argval, i.argrepr) for i in dis.get_instructions(vd)]
decomp_instrs = [(i.offset, i.opname, i.argval, i.argrepr) for i in dis.get_instructions(dp2)]

print("Orig: %d instrs, Decomp: %d instrs" % (len(orig_instrs), len(decomp_instrs)))
print()

max_len = max(len(orig_instrs), len(decomp_instrs))
diffs = []
for i in range(max_len):
    o = orig_instrs[i] if i < len(orig_instrs) else None
    d = decomp_instrs[i] if i < len(decomp_instrs) else None
    if o != d:
        diffs.append((i, o, d))

print("Total diffs: %d" % len(diffs))
print()
for idx, o, d in diffs[:50]:
    print("  [%d] orig=%s" % (idx, o))
    print("        decomp=%s" % str(d))
    print()
