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

orig_code = load_code('site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc')
cfile = py_compile.compile('site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_sourceOK.py', doraise=True, quiet=2)
with open(cfile, 'rb') as f:
    f.read(16)
    decomp_code = marshal.load(f)

orig_func = extract_func(orig_code, 'get_one_event')
decomp_func = extract_func(decomp_code, 'get_one_event')

print("=== ORIG ===")
orig_instrs = list(_filter_noise_instrs(get_bytecode_instructions(orig_func)))
for i, instr in enumerate(orig_instrs):
    print(f"  {i:3d} {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")

print("\n=== DECOMP ===")
decomp_instrs = list(_filter_noise_instrs(get_bytecode_instructions(decomp_func)))
for i, instr in enumerate(decomp_instrs):
    print(f"  {i:3d} {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")

print("\n=== DIFFS ===")
details = compare_bytecode(orig_func, decomp_func)
for td in details.get('true_diffs', []):
    print(f"  idx={td['index']}: orig={td.get('orig_op','')}({td.get('orig_arg','')}) decomp={td.get('decomp_op','')}({td.get('decomp_arg','')})")
