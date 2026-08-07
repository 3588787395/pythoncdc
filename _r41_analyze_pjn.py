import sys, types, marshal, io, dis, os, json
sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')
from base import compare_bytecode, _filter_noise_instrs
from pycdc import decompile_pyc

# Analyze POP_JUMP_IF_NOT_NONE pattern in tradingday_calendar.pyc
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

# Find get_all_trades_days
for name in sorted(orig_map.keys()):
    if 'get_all_trades_days' in name:
        print(f"\n=== {name} ===")
        cmp = compare_bytecode(orig_map[name], decomp_map.get(name))
        if not cmp.get('match') and not cmp.get('jump_only'):
            true_diffs = cmp.get('true_diffs', [])
            jump_diffs = cmp.get('jump_diffs', [])
            print(f"true_diffs: {len(true_diffs)}, jump_diffs: {len(jump_diffs)}")
            for d in true_diffs[:5]:
                print(f"  orig: {d.get('orig_op')} {d.get('orig_arg')} | decomp: {d.get('decomp_op')} {d.get('decomp_arg')}")
            for d in jump_diffs[:5]:
                print(f"  JUMP: orig: {d.get('orig_op')} {d.get('orig_arg')} | decomp: {d.get('decomp_op')} {d.get('decomp_arg')}")
            
            # Show first 40 instructions of both
            print(f"\nOriginal first 40 instructions:")
            orig_instrs = _filter_noise_instrs(orig_map[name])
            for i, instr in enumerate(orig_instrs[:40]):
                print(f"  {i}: {instr.opname} {instr.argval}")
            
            print(f"\nDecompiled first 40 instructions:")
            decomp_instrs = _filter_noise_instrs(decomp_map.get(name, orig_map[name]))
            for i, instr in enumerate(decomp_instrs[:40]):
                print(f"  {i}: {instr.opname} {instr.argval}")
        break

# Also check cgroup_utils.pyc - delete_cgroup_config
print("\n\n=== cgroup_utils.pyc - delete_cgroup_config ===")
pyc_path2 = 'site-packages/IQCommon/util/cgroup_utils.pyc'
with open(pyc_path2, 'rb') as f:
    f.read(16)
    orig_code2 = marshal.load(f)

source2 = decompile_pyc(pyc_path2)
decomp_code2 = compile(source2, '<decompiled>', 'exec')

orig_map2 = extract_code_objects(orig_code2)
decomp_map2 = extract_code_objects(decomp_code2)

for name in sorted(orig_map2.keys()):
    if 'delete_cgroup_config' in name:
        print(f"\n=== {name} ===")
        cmp = compare_bytecode(orig_map2[name], decomp_map2.get(name))
        if not cmp.get('match') and not cmp.get('jump_only'):
            true_diffs = cmp.get('true_diffs', [])
            print(f"true_diffs: {len(true_diffs)}")
            for d in true_diffs[:10]:
                print(f"  orig: {d.get('orig_op')} {d.get('orig_arg')} | decomp: {d.get('decomp_op')} {d.get('decomp_arg')}")
            
            # Show first 30 instructions of both
            print(f"\nOriginal first 30 instructions:")
            orig_instrs = _filter_noise_instrs(orig_map2[name])
            for i, instr in enumerate(orig_instrs[:30]):
                print(f"  {i}: {instr.opname} {instr.argval}")
            
            print(f"\nDecompiled first 30 instructions:")
            decomp_instrs = _filter_noise_instrs(decomp_map2.get(name, orig_map2[name]))
            for i, instr in enumerate(decomp_instrs[:30]):
                print(f"  {i}: {instr.opname} {instr.argval}")
        break
