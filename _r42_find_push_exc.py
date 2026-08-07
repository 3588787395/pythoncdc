import sys, types, marshal, io, dis, os, json
sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')
from base import compare_bytecode
from pycdc import decompile_pyc

# Find files with PUSH_EXC_INFO pattern
with open('pyc_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def extract_code_objects(code, prefix=''):
    result = {prefix or code.co_name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const, f"{prefix}.{const.co_name}" if prefix else const.co_name))
    return result

push_exc_files = []

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
    
    common = set(orig_map.keys()) & set(decomp_map.keys())
    push_exc_count = 0
    
    for name in sorted(common):
        cmp = compare_bytecode(orig_map[name], decomp_map[name])
        if not cmp.get('match') and not cmp.get('jump_only'):
            true_diffs = cmp.get('true_diffs', [])
            if true_diffs:
                first = true_diffs[0]
                orig_op = first.get('orig_op', '?')
                if orig_op == 'PUSH_EXC_INFO':
                    push_exc_count += 1
    
    if push_exc_count > 0:
        push_exc_files.append((rate, path, push_exc_count))

push_exc_files.sort()

print("=== Files with PUSH_EXC_INFO as first true_diff (lowest rate first) ===")
for rate, path, count in push_exc_files[:15]:
    basename = os.path.basename(path)
    print(f"  {basename}: {rate*100:.2f}% ({count} funcs)")
