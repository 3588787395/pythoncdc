import json

idx = json.load(open('pyc_index.json', 'r', encoding='utf-8'))
ok = [e for e in idx if e['decompile_status'] == 'ok']
partial = [e for e in idx if e['decompile_status'] == 'partial']
failed = [e for e in idx if e['decompile_status'] == 'failed']
pending = [e for e in idx if e['decompile_status'] == 'pending']

total_funcs = sum(e['function_count'] for e in idx)
matched_funcs = sum(int(e['function_count'] * e['bytecode_match_rate']) for e in idx)

print(f"Total: {len(idx)}, OK: {len(ok)}, Partial: {len(partial)}, Failed: {len(failed)}, Pending: {len(pending)}")
print(f"Total funcs: {total_funcs}, Matched: {matched_funcs}, Rate: {matched_funcs/total_funcs*100:.2f}%")
print()

# Show not-ok files sorted by match rate ascending
not_ok = [e for e in idx if e['decompile_status'] != 'ok']
not_ok.sort(key=lambda x: x['bytecode_match_rate'])
print("=== Not OK files (all) ===")
for e in not_ok:
    short_path = e['path'].split('site-packages/')[-1]
    print(f"  {e['decompile_status']:8s} {e['bytecode_match_rate']:.4f}  funcs={e['function_count']:3d}  {short_path}")
