import ast, dis, marshal

# Original
f = open('decompiler_test_comprehensive.cpython-311.pyc', 'rb')
f.read(16)
code = marshal.load(f)
dp = [c for c in code.co_consts if hasattr(c, 'co_name') and c.co_name == 'DataProcessor'][0]
vd = [c for c in dp.co_consts if hasattr(c, 'co_name') and c.co_name == 'validate_data'][0]

# Decompiled
f2 = open('_r108_validate_out.py', 'r', encoding='utf-8', errors='replace')
src = f2.read()
tree = ast.parse(src)
cls = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == 'DataProcessor'][0]
mod = ast.Module(body=[ast.ClassDef(name='DP', bases=[], keywords=[], body=cls.body, decorator_list=[])], type_ignores=[])
mod2 = ast.fix_missing_locations(mod)
comp = compile(mod2, '<x>', 'exec')
dp2 = [c for c in comp.co_consts if hasattr(c, 'co_name') and c.co_name == 'validate_data'][0]

# Get instruction lists
def get_instrs(codeobj):
    return [(i.offset, i.opname, i.argval, i.argrepr) for i in dis.get_instructions(codeobj)]

orig = get_instrs(vd)
decomp = get_instrs(dp2)

print("=== ORIGINAL ===")
for o in orig:
    print(o)
print("\n=== DECOMPILED ===")
for o in decomp:
    print(o)
print(f"\nOrig instrs: {len(orig)}, Decomp instrs: {len(decomp)}")
