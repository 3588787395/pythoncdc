import sys, types, marshal, io, dis, os
sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')
from base import compare_bytecode, _filter_noise_instrs
from pycdc import decompile_pyc

pyc_path = 'site-packages/IQEngine/core/bar.pyc'

with open(pyc_path, 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

source = decompile_pyc(pyc_path)
decomp_code = compile(source, '<decompiled>', 'exec')

def extract_code_objects(code, prefix=''):
    result = {prefix or code.co_name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const, f"{prefix}.{const.co_name}" if prefix else const.co_name))
    return result

orig_map = extract_code_objects(orig_code)
decomp_map = extract_code_objects(decomp_code)

# Find BarDict.__getitem__
target_name = None
for name in sorted(orig_map.keys()):
    if '__getitem__' in name and 'BarDict' in name:
        target_name = name
        break

if not target_name:
    print("BarDict.__getitem__ not found")
    sys.exit(1)

print(f"=== {target_name} ===")
print(f"\nOriginal co_varnames: {orig_map[target_name].co_varnames}")
print(f"Decompiled co_varnames: {decomp_map.get(target_name, orig_map[target_name]).co_varnames}")

# Show original bytecode
print(f"\nOriginal bytecode:")
buf = io.StringIO()
dis.dis(orig_map[target_name], file=buf)
for line in buf.getvalue().split('\n')[:60]:
    print(f"  {line}")

# Show decompiled source
print(f"\nDecompiled source:")
lines = source.split('\n')
in_func = False
for i, line in enumerate(lines):
    if 'class BarDict' in line:
        in_func = True
    if in_func and '__getitem__' in line:
        for j in range(i, min(i+30, len(lines))):
            print(f"  {j}: {lines[j]}")
        break

# Compare
cmp = compare_bytecode(orig_map[target_name], decomp_map.get(target_name))
if not cmp.get('match'):
    true_diffs = cmp.get('true_diffs', [])
    print(f"\ntrue_diffs: {len(true_diffs)}")
    for d in true_diffs[:15]:
        print(f"  orig: {d.get('orig_op')} {d.get('orig_arg')} | decomp: {d.get('decomp_op')} {d.get('decomp_arg')}")
