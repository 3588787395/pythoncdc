import sys, types, marshal, io, dis, os
sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')
from base import compare_bytecode
from pycdc import decompile_pyc

pyc_path = 'site-packages/IQData/config/config.pyc'

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

# Show <module> first 20 true_diffs
name = '<module>'
cmp = compare_bytecode(orig_map[name], decomp_map.get(name))
true_diffs = cmp.get('true_diffs', [])
print(f"<module> true_diffs: {len(true_diffs)}")
for d in true_diffs[:20]:
    print(f"  orig: {d.get('orig_op')} {d.get('orig_arg')} | decomp: {d.get('decomp_op')} {d.get('decomp_arg')}")

# Show decompiled source first 40 lines
print("\n=== Decompiled source (first 40 lines) ===")
lines = source.split('\n')
for i, line in enumerate(lines[:40]):
    print(f"  {i}: {line}")

# Show original bytecode first 60 lines
print("\n=== Original bytecode (first 60 lines) ===")
buf = io.StringIO()
dis.dis(orig_code, file=buf)
for line in buf.getvalue().split('\n')[:60]:
    print(f"  {line}")
