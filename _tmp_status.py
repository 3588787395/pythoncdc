import json

idx = json.load(open('pyc_index.json', 'r', encoding='utf-8'))
ok_count = sum(1 for e in idx if e.get('decompile_status') == 'ok')
partial_count = sum(1 for e in idx if e.get('decompile_status') == 'partial')
failed_count = sum(1 for e in idx if e.get('decompile_status') == 'failed')
total_funcs = sum(e.get('function_count', 0) for e in idx)
ok_funcs = sum(e.get('function_count', 0) for e in idx if e.get('decompile_status') == 'ok')
partial_funcs = sum(e.get('function_count', 0) for e in idx if e.get('decompile_status') == 'partial')

print(f"OK: {ok_count} files ({ok_funcs} funcs)")
print(f"Partial: {partial_count} files ({partial_funcs} funcs)")
print(f"Failed: {failed_count} files")
print(f"Total: {len(idx)} files ({total_funcs} funcs)")
print(f"Overall match rate: {(ok_funcs + 0) / total_funcs * 100:.2f}% (OK only)")
print()

# List partial files sorted by match rate (lowest first)
partials = [e for e in idx if e.get('decompile_status') == 'partial']
partials.sort(key=lambda e: e.get('bytecode_match_rate', 0))
print(f"Lowest 20 partial files:")
for e in partials[:20]:
    path = e['path']
    if len(path) > 70:
        path = '...' + path[-67:]
    mr = e.get('bytecode_match_rate', 0)
    fc = e.get('function_count', 0)
    ltr = e.get('last_tested_round', 0)
    print(f"  {path}: {mr:.4f} ({fc} funcs, round {ltr})")
