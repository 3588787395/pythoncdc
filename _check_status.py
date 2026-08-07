import json

idx = json.load(open('pyc_index.json', encoding='utf-8'))
stats = {}
for e in idx:
    s = e['decompile_status']
    stats[s] = stats.get(s, 0) + 1
print(f"Total: {len(idx)}")
print(f"Status: {stats}")

not_ok = [e for e in idx if e['decompile_status'] != 'ok']
print(f"\nNot OK: {len(not_ok)}")

# Sort by path
not_ok.sort(key=lambda e: e['path'])
for e in not_ok[:30]:
    print(f"  {e['path']}: {e['decompile_status']} rate={e['bytecode_match_rate']:.4f} round={e.get('last_tested_round', 0)}")

# Calculate cumulative match
total_funcs = sum(e.get('function_count', 0) for e in idx)
ok_funcs = sum(e.get('function_count', 0) * e['bytecode_match_rate'] for e in idx)
print(f"\nCumulative match rate: {ok_funcs/total_funcs*100:.2f}% ({int(ok_funcs)}/{total_funcs})")
