import sys, types, marshal, io, dis, os, json
sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')
from base import compare_bytecode, _filter_noise_instrs
from pycdc import decompile_pyc

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
    rate = entry.get('bytecode_match_rate', 0.0)
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
                    if first.get('orig_op') is None and first.get('decomp_op') == 'LOAD_CONST':
                        found.append((rate, path, name, len(true_diffs)))
                        if len(found) <= 3:
                            print(f"=== {name} in {os.path.basename(path)} (td={len(true_diffs)}) ===")
                            for d in true_diffs[:5]:
                                print(f"  orig: {d.get('orig_op')} | decomp: {d.get('decomp_op')} {d.get('decomp_arg')}")
                            orig_instrs = _filter_noise_instrs(list(dis.get_instructions(orig_map[name])))
                            decomp_instrs = _filter_noise_instrs(list(dis.get_instructions(decomp_map[name])))
                            # The diff is at the END (orig has fewer instructions)
                            print(f"  orig_count={len(orig_instrs)}, decomp_count={len(decomp_instrs)}")
                            # Show last 5 instructions of each
                            print(f"  Last 5 orig:")
                            for i in range(max(0,len(orig_instrs)-5), len(orig_instrs)):
                                print(f"    [{i}] {orig_instrs[i].opname} {orig_instrs[i].argval}")
                            print(f"  Last 5 decomp:")
                            for i in range(max(0,len(decomp_instrs)-5), len(decomp_instrs)):
                                print(f"    [{i}] {decomp_instrs[i].opname} {decomp_instrs[i].argval}")
                            print()

found.sort()
print(f"\n=== All ?->LOAD_CONST cases ({len(found)}) ===")
for rate, path, name, td in found[:15]:
    print(f"  {os.path.basename(path)}: {name} (rate={rate*100:.1f}%, td={td})")
