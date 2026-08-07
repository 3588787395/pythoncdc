import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
from scripts.pyc_batch_verify import decompile_single, bytecode_diff

pyc_path = 'site-packages/IQEngine/utils/trade_schedule.pyc'
result = decompile_single(pyc_path)
print(f"Decompile success: {result['success']}")
if result['error']:
    print(f"Error: {result['error']}")

ok_py_path = result['ok_py_path']
diff = bytecode_diff(pyc_path, ok_py_path)
print(f"\nTotal functions: {diff['total_functions']}")
print(f"Matched: {diff['matched_functions']}")
print(f"Rate: {diff['match_rate']:.4f}")
print(f"\nMismatches:")
for m in diff['mismatches']:
    print(f"  {m['name']}: orig={m['orig_count']} decomp={m['decomp_count']}")
    if m.get('first_diff'):
        print(f"    first_diff: {m['first_diff']}")
print(f"\nMissing in decomp: {diff['missing_in_decomp']}")
print(f"Extra in decomp: {diff['extra_in_decomp']}")
