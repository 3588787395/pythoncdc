"""Detailed diff of exception_handling_complex bytecode."""
import ast, dis, marshal

# Original
f = open('decompiler_test_comprehensive.cpython-311.pyc', 'rb')
f.read(16)
code = marshal.load(f)
dp = [c for c in code.co_consts if hasattr(c, 'co_name') and c.co_name == 'DataProcessor'][0]
ehc = [c for c in dp.co_consts if hasattr(c, 'co_name') and c.co_name == 'exception_handling_complex'][0]

# Decompiled
f2 = open('_r108_out5.py', 'r', encoding='utf-8', errors='replace')
src = f2.read()
tree = ast.parse(src)
cls = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == 'DataProcessor'][0]
new_cls = ast.ClassDef(name='DP', bases=[], keywords=[], body=cls.body, decorator_list=[])
mod = ast.Module(body=[new_cls], type_ignores=[])
mod = ast.fix_missing_locations(mod)
comp = compile(mod, '<x>', 'exec')

dp2 = None
for c in comp.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'DP':
        for cc in c.co_consts:
            if hasattr(cc, 'co_name') and cc.co_name == 'exception_handling_complex':
                dp2 = cc
                break
    if dp2:
        break

if dp2 is None:
    print("ERROR: not found")
    exit(1)

orig = [(i.offset, i.opname, i.argval) for i in dis.get_instructions(ehc)]
decomp = [(i.offset, i.opname, i.argval) for i in dis.get_instructions(dp2)]

# Print side by side
print("=== ORIG (203 instrs) ===")
for o in orig:
    print("  %4d %s %s" % (o[0], o[1], o[2] if o[2] is not None else ''))
print()
print("=== DECOMP (%d instrs) ===" % len(decomp))
for d in decomp:
    print("  %4d %s %s" % (d[0], d[1], d[2] if d[2] is not None else ''))
