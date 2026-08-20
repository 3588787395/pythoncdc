"""Comprehensive validation: compare all functions bytecode."""
import sys, marshal, dis, ast
sys.path.insert(0, '.')

f = open('decompiler_test_comprehensive.cpython-311.pyc', 'rb')
f.read(16)
code = marshal.load(f)

# Get all functions from original
orig_funcs = {}
for c in code.co_consts:
    if hasattr(c, 'co_name'):
        orig_funcs[c.co_name] = c
        for cc in c.co_consts:
            if hasattr(cc, 'co_name'):
                orig_funcs[c.co_name + '.' + cc.co_name] = cc

# Load decompiled
f2 = open('_r108_out5.py', 'r', encoding='utf-8', errors='replace')
src = f2.read()
tree = ast.parse(src)

decomp_funcs = {}
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        decomp_funcs[node.name] = node
    elif isinstance(node, ast.ClassDef):
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                decomp_funcs[node.name + '.' + item.name] = item

matched = 0
total = 0
for name, orig_code in sorted(orig_funcs.items()):
    if name not in decomp_funcs:
        print(f"MISSING: {name}")
        continue
    total += 1
    func_node = decomp_funcs[name]
    # Wrap and compile
    try:
        mod = ast.Module(body=[func_node], type_ignores=[])
        mod = ast.fix_missing_locations(mod)
        comp = compile(mod, '<x>', 'exec')
        decomp_code = comp
    except Exception as e:
        print(f"COMPILE_ERROR: {name}: {e}")
        continue
    
    orig_instrs = [(i.opname, i.argval) for i in dis.get_instructions(orig_code)]
    decomp_instrs = [(i.opname, i.argval) for i in dis.get_instructions(decomp_code)]
    
    if orig_instrs == decomp_instrs:
        matched += 1
        print(f"MATCH: {name} ({len(orig_instrs)} instrs)")
    else:
        diffs = sum(1 for a, b in zip(orig_instrs, decomp_instrs) if a != b)
        diffs += abs(len(orig_instrs) - len(decomp_instrs))
        print(f"DIFF: {name} ({diffs} diffs, orig={len(orig_instrs)} decomp={len(decomp_instrs)})")

print(f"\n=== {matched}/{total} matched ({100*matched/total:.1f}%) ===")
