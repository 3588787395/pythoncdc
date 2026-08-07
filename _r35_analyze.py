"""R35 测试工程师：分析 trade_live_broker.pyc 的字节码差异模式"""
import sys, os, dis, types, marshal, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from testqouter.round1.base import decompile_pyc, get_bytecode_instructions, compare_bytecode, _normalize_argval

pyc_path = "site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc"

# Load original code
with open(pyc_path, 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

# Decompile
source = decompile_pyc(pyc_path)
decomp_code = compile(source, '<decompiled>', 'exec')

# Extract all code objects
def extract_codes(code, prefix=""):
    result = {prefix + code.co_name: code}
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            result.update(extract_codes(c, prefix + code.co_name + "."))
    return result

orig_funcs = extract_codes(orig_code)
decomp_funcs = extract_codes(decomp_code)

# Compare
mismatches = []
matched = 0
nop_noise = 0
resume_noise = 0
ext_arg_noise = 0
real_diff = 0

for name, orig_fc in orig_funcs.items():
    if name not in decomp_funcs:
        mismatches.append((name, "MISSING_IN_DECOMP", 0))
        continue
    decomp_fc = decomp_funcs[name]
    result = compare_bytecode(orig_fc, decomp_fc)
    if result['match'] or result.get('jump_only'):
        matched += 1
    else:
        td = result['true_diffs']
        jd = result['jump_diffs']
        
        # Classify the mismatch
        has_nop = any(d.get('orig_op') == 'NOP' or d.get('decomp_op') == 'NOP' for d in td)
        has_resume = any(d.get('orig_op') == 'RESUME' or d.get('decomp_op') == 'RESUME' for d in td)
        has_ext_arg = any(d.get('orig_op') == 'EXTENDED_ARG' and d.get('decomp_op') == 'EXTENDED_ARG' for d in td)
        
        if has_nop:
            nop_noise += 1
        if has_resume:
            resume_noise += 1
        if has_ext_arg:
            ext_arg_noise += 1
        if not has_nop and not has_resume and not has_ext_arg:
            real_diff += 1
        
        # Get first few true_diffs
        first_diffs = td[:3]
        mismatches.append((name, f"td={len(td)} jd={len(jd)}", first_diffs))

print(f"Total functions: {len(orig_funcs)}")
print(f"Matched: {matched}")
print(f"Mismatched: {len(mismatches)}")
print(f"  NOP noise: {nop_noise}")
print(f"  RESUME noise: {resume_noise}")
print(f"  EXTENDED_ARG noise: {ext_arg_noise}")
print(f"  Real diff (no NOP/RESUME/EXT_ARG): {real_diff}")
print()

# Show first 15 mismatches with details
print("=== Mismatch details (first 15) ===")
for name, info, *extra in mismatches[:15]:
    print(f"  {name}: {info}")
    if extra and extra[0]:
        for d in extra[0][:2]:
            print(f"    -> idx={d.get('index')} orig={d.get('orig_op')}({d.get('orig_arg')}) decomp={d.get('decomp_op')}({d.get('decomp_arg')})")
