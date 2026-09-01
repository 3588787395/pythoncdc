import sys, json, marshal, types, py_compile, os
sys.path.insert(0, '.')
from testqouter.round1.base import compare_bytecode, _filter_noise_instrs, get_bytecode_instructions

def _load_pyc_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def _extract_code_objects(code, prefix=''):
    result = {}
    key = prefix + code.co_name
    result[key] = code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(_extract_code_objects(const, prefix + code.co_name + '.'))
    return result

with open('pyc_index.json', 'r', encoding='utf-8') as f:
    index = json.load(f)

count = 0
for entry in index:
    if entry.get('decompile_status') != 'partial':
        continue
    pyc_path = entry['path']
    ok_py_path = pyc_path[:-4] + 'OK.py'
    if not os.path.exists(ok_py_path):
        continue
    orig_code = _load_pyc_code(pyc_path)
    try:
        cfile = py_compile.compile(ok_py_path, doraise=True, quiet=2)
    except:
        continue
    with open(cfile, 'rb') as f:
        f.read(16)
        decomp_code = marshal.load(f)
    orig_map = _extract_code_objects(orig_code)
    decomp_map = _extract_code_objects(decomp_code)
    common = set(orig_map.keys()) & set(decomp_map.keys())
    for name in sorted(common):
        details = compare_bytecode(orig_map[name], decomp_map[name])
        if details.get('match') or details.get('jump_only'):
            continue
        true_diffs = details.get('true_diffs', [])
        for td in true_diffs:
            if 'JUMP_BACKWARD' in td.get('orig_op', '') and 'JUMP_FORWARD' in td.get('decomp_op', ''):
                idx = td['index']
                orig_instrs = list(_filter_noise_instrs(get_bytecode_instructions(orig_map[name])))
                decomp_instrs = list(_filter_noise_instrs(get_bytecode_instructions(decomp_map[name])))
                # Check if there's a JUMP_BACKWARD later in decomp
                has_later_jb = False
                for j in range(idx+1, len(decomp_instrs)):
                    if decomp_instrs[j].opname.startswith('JUMP_BACKWARD'):
                        has_later_jb = True
                        break
                p = entry['path'].split('site-packages')[-1]
                print("%s  %s  idx=%d  later_jb=%s  orig_context=[%s %s %s] decomp_context=[%s %s %s]" % (
                    p, name.split('.')[-1], idx, has_later_jb,
                    orig_instrs[max(0,idx-1):idx][0].opname if idx>0 else '-',
                    orig_instrs[idx].opname,
                    orig_instrs[idx+1].opname if idx+1<len(orig_instrs) else '-',
                    decomp_instrs[max(0,idx-1):idx][0].opname if idx>0 else '-',
                    decomp_instrs[idx].opname,
                    decomp_instrs[idx+1].opname if idx+1<len(decomp_instrs) else '-',
                ))
                count += 1
                if count >= 30:
                    break
        if count >= 30:
            break
    if count >= 30:
        break
