"""R17 诊断：枚举 <module> 中所有 LOAD_CONST code 对象，检查其是否对应已独立比较的函数。"""
import sys, types, dis
sys.path.insert(0, '/workspace')
sys.path.insert(0, '/workspace/.trae/specs/region-reduction-quotation-10rounds-v2/rounds/round_17/test_engineer')
from exact_match_stats import get_instr_list, walk_code, load_orig, PYC, DECOMPILED

import json

with open('/tmp/r17_out/bc_results.json') as f:
    bc = json.load(f)
results = bc['results']

orig_top = load_orig()
orig_cos = walk_code(orig_top)
with open(DECOMPILED, 'r', encoding='utf-8') as f:
    src = f.read()
new_code = compile(src, '<decompiled>', 'exec')
new_cos = walk_code(new_code)

oa = get_instr_list(orig_cos['<module>'])
na = get_instr_list(new_cos['<module>'])

print(f"<module> orig_len={len(oa)} new_len={len(na)} (diff={len(na)-len(oa):+d})")
print()
print("=== All LOAD_CONST code objects in <module> ===")
print(f"{'idx':>4} {'orig_name':<30} {'new_name':<30} {'orig_indep':<12} {'new_indep':<12} {'indep_status':<14} {'len_eq':<8}")

code_obj_indices = []
for i, (a, b) in enumerate(zip(oa, na)):
    av_a, av_b = a[2], b[2]
    if isinstance(av_a, types.CodeType) and isinstance(av_b, types.CodeType):
        name_a = av_a.co_name
        name_b = av_b.co_name
        # 查找该 code 对象在 walk_code 结果中对应的独立函数名
        # 顶层函数在 <module> 下，独立比较时名称就是 co_name
        indep_name_a = name_a  # 顶层函数名
        indep_name_b = name_b
        in_results = indep_name_a in results
        indep_status = results.get(indep_name_a, {}).get('status', 'NOT_FOUND') if in_results else 'NOT_FOUND'
        len_a = len(get_instr_list(av_a))
        len_b = len(get_instr_list(av_b))
        len_eq = (len_a == len_b)
        code_obj_indices.append((i, name_a, name_b, indep_status, len_a, len_b, len_eq))
        print(f"{i:>4} {name_a:<30} {name_b:<30} {str(in_results):<12} {str(indep_name_b in results):<12} {indep_status:<14} {str(len_eq):<8} ({len_a} vs {len_b})")

print()
print("=== Summary ===")
total_code_objs = len(code_obj_indices)
delegated = sum(1 for c in code_obj_indices if c[3] in ('match', 'len_diff', 'instr_diff', 'missing'))
delegated_mismatch = sum(1 for c in code_obj_indices if c[3] in ('len_diff', 'instr_diff', 'missing'))
delegated_match = sum(1 for c in code_obj_indices if c[3] == 'match')
print(f"total code objects embedded: {total_code_objs}")
print(f"code objects corresponding to independently-compared functions: {delegated}")
print(f"  - of which match: {delegated_match}")
print(f"  - of which mismatched (would be delegated): {delegated_mismatch}")
print()
print("=== First code object that fails (transitive mismatch source) ===")
# 找到第一个 instr_equal 失败的 code 对象
from exact_match_stats import instr_equal
for i, (a, b) in enumerate(zip(oa, na)):
    av_a, av_b = a[2], b[2]
    if isinstance(av_a, types.CodeType) and isinstance(av_b, types.CodeType):
        if not instr_equal(a, b, ctx=(oa, na, i)):
            indep_status = results.get(av_a.co_name, {}).get('status', 'NOT_FOUND')
            print(f"  idx {i}: <code {av_a.co_name}> instr_equal=False, independent status={indep_status}")
            break
