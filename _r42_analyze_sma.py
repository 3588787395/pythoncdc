import sys, types, marshal, io, dis, os
sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')
from base import compare_bytecode
from pycdc import decompile_pyc

pyc_path = 'site-packages/IQEngine/plugins/plugin_system_trade/send_message_api.pyc'

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

# Find mismatched functions
for name in sorted(orig_map.keys()):
    if name in decomp_map:
        cmp = compare_bytecode(orig_map[name], decomp_map[name])
        if not cmp.get('match') and not cmp.get('jump_only'):
            true_diffs = cmp.get('true_diffs', [])
            if true_diffs and true_diffs[0].get('orig_op') == 'PUSH_EXC_INFO':
                print(f"=== {name} (true_diffs={len(true_diffs)}) ===")
                for d in true_diffs[:10]:
                    print(f"  orig: {d.get('orig_op')} {d.get('orig_arg')} | decomp: {d.get('decomp_op')} {d.get('decomp_arg')}")
                
                # Show original bytecode
                print(f"\nOriginal bytecode:")
                buf = io.StringIO()
                dis.dis(orig_map[name], file=buf)
                for line in buf.getvalue().split('\n')[:50]:
                    print(f"  {line}")
                
                # Show decompiled source
                print(f"\nDecompiled source:")
                lines = source.split('\n')
                in_func = False
                for i, line in enumerate(lines):
                    if name.split('.')[-1] in line and 'def ' in line:
                        in_func = True
                    if in_func:
                        print(f"  {i}: {line}")
                        if in_func and i > 0 and line.strip().startswith('def ') and name.split('.')[-1] not in line:
                            break
                break
