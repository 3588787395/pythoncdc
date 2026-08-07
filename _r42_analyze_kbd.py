import sys, types, marshal, io, dis, os
sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')
from base import compare_bytecode, _filter_noise_instrs
from pycdc import decompile_pyc

pyc_path = 'site-packages/IQCommon/api/klinedata.pyc'

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

name = 'get_kline_by_date_new'
cmp = compare_bytecode(orig_map[name], decomp_map[name])
true_diffs = cmp.get('true_diffs', [])
print(f"{name}: match={cmp.get('match')}, jump_only={cmp.get('jump_only')}, true_diffs={len(true_diffs)}")

# Show all true_diffs
print(f"\n=== All {len(true_diffs)} true_diffs ===")
for i, d in enumerate(true_diffs):
    print(f"  [{i}] orig: {d.get('orig_op')} {d.get('orig_arg')} | decomp: {d.get('decomp_op')} {d.get('decomp_arg')}")

# Show original instructions around the first diff
orig_instrs = _filter_noise_instrs(list(dis.get_instructions(orig_map[name])))
decomp_instrs = _filter_noise_instrs(list(dis.get_instructions(decomp_map[name])))

# Find the first diff position
first_diff_pos = None
for i in range(min(len(orig_instrs), len(decomp_instrs))):
    o = orig_instrs[i]
    d = decomp_instrs[i]
    o_norm = o.argval if o.argval is not None else o.arg
    d_norm = d.argval if d.argval is not None else d.arg
    # Normalize LOAD_ATTR vs LOAD_METHOD
    if o.opname == 'LOAD_ATTR' and d.opname == 'LOAD_METHOD':
        continue
    if o.opname == 'LOAD_METHOD' and d.opname == 'LOAD_ATTR':
        continue
    if o.opname != d.opname or o_norm != d_norm:
        first_diff_pos = i
        break

if first_diff_pos is not None:
    print(f"\n=== First diff at position {first_diff_pos} ===")
    start = max(0, first_diff_pos - 5)
    end = min(len(orig_instrs), first_diff_pos + 20)
    print("Original:")
    for i in range(start, end):
        marker = " >>>" if i == first_diff_pos else "    "
        print(f"  {marker} [{i}] {orig_instrs[i].opname} {orig_instrs[i].argval}")
    
    print("Decompiled:")
    for i in range(start, min(len(decomp_instrs), end)):
        marker = " >>>" if i == first_diff_pos else "    "
        print(f"  {marker} [{i}] {decomp_instrs[i].opname} {decomp_instrs[i].argval}")
