import sys
sys.path.insert(0, '.')
from testqouter.round1.base import compare_bytecode, _filter_noise_instrs, get_bytecode_instructions
import marshal, types, py_compile

def load_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def extract_func(code, name):
    if code.co_name == name:
        return code
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            r = extract_func(c, name)
            if r: return r
    return None

orig_code = load_code('site-packages/fly/common/tradingday_calendar.pyc')
cfile = py_compile.compile('site-packages/fly/common/tradingday_calendarOK.py', doraise=True, quiet=2)
with open(cfile, 'rb') as f:
    f.read(16)
    decomp_code = marshal.load(f)

orig_func = extract_func(orig_code, 'get_start_day')
decomp_func = extract_func(decomp_code, 'get_start_day')

details = compare_bytecode(orig_func, decomp_func)
for td in details.get('true_diffs', []):
    idx = td['index']
    print(f'idx={idx}: orig={td["orig_op"]}({td.get("orig_arg","")}) decomp={td["decomp_op"]}({td.get("decomp_arg","")})')

orig_instrs = list(_filter_noise_instrs(get_bytecode_instructions(orig_func)))
decomp_instrs = list(_filter_noise_instrs(get_bytecode_instructions(decomp_func)))
idx = details['true_diffs'][0]['index']
print(f'--- orig[{max(0,idx-2)}..{idx+3}] ---')
for i in range(max(0,idx-2), min(len(orig_instrs), idx+4)):
    print(f'  {i:3d} {orig_instrs[i].offset:4d} {orig_instrs[i].opname:30s} {orig_instrs[i].argrepr}')
print(f'--- decomp[{max(0,idx-2)}..{idx+3}] ---')
for i in range(max(0,idx-2), min(len(decomp_instrs), idx+4)):
    print(f'  {i:3d} {decomp_instrs[i].offset:4d} {decomp_instrs[i].opname:30s} {decomp_instrs[i].argrepr}')
