import sys, types, marshal, io, dis, os, json
sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')
from base import compare_bytecode
from pycdc import decompile_pyc

# Find files with COPY_FREE_VARS pattern
with open('pyc_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def extract_code_objects(code, prefix=''):
    result = {prefix or code.co_name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const, f"{prefix}.{const.co_name}" if prefix else const.co_name))
    return result

found = []

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
                if true_diffs and true_diffs[0].get('orig_op') == 'COPY_FREE_VARS':
                    found.append((path, name, len(true_diffs)))
                    # Show details for first one
                    if len(found) == 1:
                        print(f"=== {name} in {os.path.basename(path)} (true_diffs={len(true_diffs)}) ===")
                        for d in true_diffs[:10]:
                            print(f"  orig: {d.get('orig_op')} {d.get('orig_arg')} | decomp: {d.get('decomp_op')} {d.get('decomp_arg')}")
                        
                        # Show first 20 instructions of both
                        print(f"\nOriginal first 20 instructions:")
                        orig_instrs = list(dis.get_instructions(orig_map[name]))
                        for i, instr in enumerate(orig_instrs[:20]):
                            print(f"  {i}: {instr.opname} {instr.argval}")
                        
                        print(f"\nDecompiled first 20 instructions:")
                        decomp_instrs = list(dis.get_instructions(decomp_map[name]))
                        for i, instr in enumerate(decomp_instrs[:20]):
                            print(f"  {i}: {instr.opname} {instr.argval}")

print(f"\n\n=== All COPY_FREE_VARS cases ({len(found)}) ===")
for path, name, td in found:
    print(f"  {os.path.basename(path)}: {name} (true_diffs={td})")
