import sys, types, marshal, io, dis, os, json
sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')
from base import compare_bytecode, _filter_noise_instrs
from pycdc import decompile_pyc

# Check RESUME argument differences
with open('pyc_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def extract_code_objects(code, prefix=''):
    result = {prefix or code.co_name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const, f"{prefix}.{const.co_name}" if prefix else const.co_name))
    return result

# Count RESUME argument patterns
resume_diffs = []
same_op_const = []

for entry in data:
    if entry.get('decompile_status') != 'partial':
        continue
    path = entry.get('path', '')
    
    try:
        with open(path, 'rb') as f:
            f.read(16)
            orig_code = marshal.load(f)
        source = decompile_pyc(path)
        decomp_code = compile(source, '<decompiled>', 'exec')
    except:
        continue
    
    orig_map = extract_code_objects(orig_code)
    decomp_map = extract_code_objects(decomp_code)
    
    for name in sorted(orig_map.keys()):
        if name in decomp_map:
            cmp = compare_bytecode(orig_map[name], decomp_map[name])
            if not cmp.get('match') and not cmp.get('jump_only'):
                true_diffs = cmp.get('true_diffs', [])
                if true_diffs:
                    first = true_diffs[0]
                    orig_op = first.get('orig_op', '?')
                    decomp_op = first.get('decomp_op', '?')
                    # Check RESUME diffs
                    if orig_op == 'RESUME' or decomp_op == 'RESUME':
                        resume_diffs.append((path, name, first))
                    # Check SAME_OP:LOAD_CONST (same opcode, different argval)
                    if orig_op == decomp_op == 'LOAD_CONST':
                        same_op_const.append((path, name, first.get('orig_arg'), first.get('decomp_arg')))

print(f"=== RESUME diffs ({len(resume_diffs)}) ===")
for path, name, d in resume_diffs[:5]:
    print(f"  {os.path.basename(path)}: {name} -> orig: {d.get('orig_op')} {d.get('orig_arg')} | decomp: {d.get('decomp_op')} {d.get('decomp_arg')}")

print(f"\n=== SAME_OP:LOAD_CONST diffs ({len(same_op_const)}) ===")
for path, name, oa, da in same_op_const[:10]:
    oa_str = str(oa)[:60]
    da_str = str(da)[:60]
    print(f"  {os.path.basename(path)}: {name}")
    print(f"    orig: {oa_str}")
    print(f"    decomp: {da_str}")
