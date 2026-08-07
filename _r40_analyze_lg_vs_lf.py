import sys, types, marshal, io, dis, os
sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')
from base import compare_bytecode, _filter_noise_instrs
from pycdc import decompile_pyc

# Analyze strategy.pyc - Strategy.initialize
pyc_path = 'site-packages/IQEngine/core/strategy/strategy.pyc'

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

# Find Strategy.initialize
for name in sorted(orig_map.keys()):
    if 'initialize' in name and 'Strategy' in name:
        print(f"\n=== {name} ===")
        cmp = compare_bytecode(orig_map[name], decomp_map.get(name))
        if not cmp.get('match') and not cmp.get('jump_only'):
            true_diffs = cmp.get('true_diffs', [])
            print(f"true_diffs: {len(true_diffs)}")
            # Show first 10 true diffs
            for d in true_diffs[:10]:
                print(f"  orig: {d.get('orig_op')} {d.get('orig_arg')} | decomp: {d.get('decomp_op')} {d.get('decomp_arg')}")
            
            # Also show first 30 instructions of both
            print(f"\nOriginal first 30 instructions:")
            orig_instrs = _filter_noise_instrs(orig_map[name])
            for i, instr in enumerate(orig_instrs[:30]):
                print(f"  {i}: {instr.opname} {instr.argval}")
            
            print(f"\nDecompiled first 30 instructions:")
            decomp_instrs = _filter_noise_instrs(decomp_map.get(name, orig_map[name]))
            for i, instr in enumerate(decomp_instrs[:30]):
                print(f"  {i}: {instr.opname} {instr.argval}")
        break
