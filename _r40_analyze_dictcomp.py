import sys, types, marshal, io, dis, os
sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')
from base import compare_bytecode, _filter_noise_instrs
from pycdc import decompile_pyc

pyc_path = 'site-packages/fly/common/tradingday_calendar.pyc'

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

# Find <dictcomp>
for name in sorted(orig_map.keys()):
    if 'dictcomp' in name:
        print(f"\n=== {name} ===")
        print(f"Orig co_varnames: {orig_map[name].co_varnames}")
        print(f"Decomp co_varnames: {decomp_map.get(name, orig_map[name]).co_varnames}")
        
        # Show original bytecode
        print(f"\nOriginal bytecode:")
        buf = io.StringIO()
        dis.dis(orig_map[name], file=buf)
        for line in buf.getvalue().split('\n'):
            print(f"  {line}")
        
        # Show decompiled bytecode
        if name in decomp_map:
            print(f"\nDecompiled bytecode:")
            buf = io.StringIO()
            dis.dis(decomp_map[name], file=buf)
            for line in buf.getvalue().split('\n'):
                print(f"  {line}")
        
        # Compare
        cmp = compare_bytecode(orig_map[name], decomp_map.get(name))
        if not cmp.get('match'):
            true_diffs = cmp.get('true_diffs', [])
            print(f"\ntrue_diffs: {len(true_diffs)}")
            for d in true_diffs:
                print(f"  orig: {d.get('orig_op')} {d.get('orig_arg')} | decomp: {d.get('decomp_op')} {d.get('decomp_arg')}")
        break

# Also show the decompiled source around dictcomp
print("\n\nDecompiled source (search for dict comprehension):")
lines = source.split('\n')
for i, line in enumerate(lines):
    if '{' in line and 'for' in line and 'in' in line:
        for j in range(max(0, i-2), min(i+5, len(lines))):
            print(f"  {j}: {lines[j]}")
        print()
