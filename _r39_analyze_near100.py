import sys, os, types, marshal, io, dis
sys.path.insert(0, '.')

# Import compare_bytecode from the test base
sys.path.insert(0, 'testqouter/round1')
from base import compare_bytecode, _filter_noise_instrs
from pycdc import decompile_pyc

near_100_files = [
    ('site-packages/IQEngine/core/engine/engine.pyc', 67, 68),
    ('site-packages/IQEngine/plugins/plugin_system_accounts/position_model/live_future_position.pyc', 63, 64),
    ('site-packages/IQEngine/plugins/plugin_system_accounts/account_model/option_account.pyc', 30, 31),
    ('site-packages/IQEngine/plugins/plugin_system_accounts/account_model/future_account.pyc', 29, 30),
    ('site-packages/IQEngine/core/bar.pyc', 28, 29),
    ('site-packages/IQEngine/account/order.pyc', 25, 26),
]

def extract_code_objects(code, prefix=''):
    result = {prefix or code.co_name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const, f"{prefix}.{const.co_name}" if prefix else const.co_name))
    return result

for pyc_path, matched, total in near_100_files:
    print(f"\n=== {pyc_path.split('/')[-1]} ({matched}/{total}) ===")
    
    # Load original pyc
    with open(pyc_path, 'rb') as f:
        f.read(16)
        orig_code = marshal.load(f)
    orig_map = extract_code_objects(orig_code)
    
    # Decompile
    try:
        source = decompile_pyc(pyc_path)
        decomp_code = compile(source, '<decompiled>', 'exec')
        decomp_map = extract_code_objects(decomp_code)
    except Exception as e:
        print(f"  Decompile error: {e}")
        continue
    
    # Find mismatches
    common = set(orig_map.keys()) & set(decomp_map.keys())
    for name in sorted(common):
        cmp = compare_bytecode(orig_map[name], decomp_map[name])
        if not cmp.get('match') and not cmp.get('jump_only'):
            true_diffs = cmp.get('true_diffs', [])
            jump_diffs = cmp.get('jump_diffs', [])
            if true_diffs:
                first = true_diffs[0]
                print(f"  MISMATCH: {name}")
                print(f"    true_diffs={len(true_diffs)}, jump_diffs={len(jump_diffs)}")
                print(f"    first_diff: orig={first.get('orig_op')} arg={first.get('orig_arg')} vs decomp={first.get('decomp_op')} arg={first.get('decomp_arg')}")
            elif jump_diffs:
                first = jump_diffs[0]
                print(f"  JUMP_ONLY: {name}")
                print(f"    jump_diffs={len(jump_diffs)}")
                print(f"    first_diff: orig={first.get('orig_op')} arg={first.get('orig_arg')} vs decomp={first.get('decomp_op')} arg={first.get('decomp_arg')}")
