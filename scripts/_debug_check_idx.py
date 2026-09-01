import sys, json, marshal, types, py_compile
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

for entry in json.load(open('pyc_index.json', 'r', encoding='utf-8')):
    if 'fly/data/quote.pyc' not in entry.get('path', ''):
        continue
    pyc_path = entry['path']
    ok_py_path = pyc_path[:-4] + 'OK.py'
    orig_code = _load_pyc_code(pyc_path)
    cfile = py_compile.compile(ok_py_path, doraise=True, quiet=2)
    with open(cfile, 'rb') as f:
        f.read(16)
        decomp_code = marshal.load(f)
    orig_map = _extract_code_objects(orig_code)
    decomp_map = _extract_code_objects(decomp_code)
    for name in sorted(set(orig_map.keys()) & set(decomp_map.keys())):
        if 'check_index_code' not in name:
            continue
        details = compare_bytecode(orig_map[name], decomp_map[name])
        if details.get('match'):
            continue
        td = details.get('true_diffs', [])
        print('%s: %d true_diffs' % (name.split('.')[-1], len(td)))
        for t in td:
            idx = t['index']
            print('  idx=%d: orig=%s(%s) decomp=%s(%s)' % (idx, t.get('orig_op',''), t.get('orig_arg',''), t.get('decomp_op',''), t.get('decomp_arg','')))
        
        orig_instrs = list(_filter_noise_instrs(get_bytecode_instructions(orig_map[name])))
        decomp_instrs = list(_filter_noise_instrs(get_bytecode_instructions(decomp_map[name])))
        for t in td:
            idx = t['index']
            print('  Context orig[%d-%d]:' % (max(0,idx-3), min(len(orig_instrs),idx+3)))
            for i in range(max(0,idx-3), min(len(orig_instrs),idx+3)):
                marker = '>>>' if i == idx else '   '
                print('    %s %3d %s %s' % (marker, i, orig_instrs[i].opname, orig_instrs[i].argval))
            print('  Context decomp[%d-%d]:' % (max(0,idx-3), min(len(decomp_instrs),idx+3)))
            for i in range(max(0,idx-3), min(len(decomp_instrs),idx+3)):
                marker = '>>>' if i == idx else '   '
                print('    %s %3d %s %s' % (marker, i, decomp_instrs[i].opname, decomp_instrs[i].argval))
    break
