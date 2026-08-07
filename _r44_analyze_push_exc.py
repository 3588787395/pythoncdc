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
                    if first.get('orig_op') == 'PUSH_EXC_INFO' and first.get('decomp_op') == 'RETURN_VALUE':
                        found.append((rate, path, name, len(true_diffs)))
                        if len(found) <= 2:
                            print(f"=== {name} in {os.path.basename(path)} (rate={rate*100:.1f}%, td={len(true_diffs)}) ===")
                            for d in true_diffs[:6]:
                                print(f"  orig: {d.get('orig_op')} {d.get('orig_arg')} | decomp: {d.get('decomp_op')} {d.get('decomp_arg')}")
                            orig_instrs = _filter_noise_instrs(list(dis.get_instructions(orig_map[name])))
                            decomp_instrs = _filter_noise_instrs(list(dis.get_instructions(decomp_map[name])))
                            for i in range(min(len(orig_instrs), len(decomp_instrs))):
                                o = orig_instrs[i]
                                d2 = decomp_instrs[i]
                                o_a = o.argval if o.argval is not None else o.arg
                                d_a = d2.argval if d2.argval is not None else d2.arg
                                if o.opname != d2.opname or str(o_a) != str(d_a):
                                    print(f"  First diff at [{i}]:")
                                    print(f"    orig:  {o.opname} {o_a}")
                                    print(f"    decomp: {d2.opname} {d_a}")
                                    s = max(0, i-3)
                                    print(f"    Context orig:")
                                    for j in range(s, min(i+5, len(orig_instrs))):
                                        m = ">>>" if j==i else "   "
                                        print(f"      {m} [{j}] {orig_instrs[j].opname} {orig_instrs[j].argval}")
                                    print(f"    Context decomp:")
                                    for j in range(s, min(i+5, len(decomp_instrs))):
                                        m = ">>>" if j==i else "   "
                                        print(f"      {m} [{j}] {decomp_instrs[j].opname} {decomp_instrs[j].argval}")
                                    break
                            print()

found.sort()
print(f"\n=== All PUSH_EXC_INFO->RETURN_VALUE cases ({len(found)}) ===")
for rate, path, name, td in found[:15]:
    print(f"  {os.path.basename(path)}: {name} (rate={rate*100:.1f}%, td={td})")
