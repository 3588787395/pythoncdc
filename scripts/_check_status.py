"""Check current pyc index status."""
import json
import os

idx_path = os.path.join(os.path.dirname(__file__), '..', '.trae', 'specs', 'region-comment-multi-pyc-iteration', 'pyc_index.json')
with open(idx_path, 'r') as f:
    idx = json.load(f)

stats = {}
for e in idx:
    s = e['decompile_status']
    stats[s] = stats.get(s, 0) + 1

print(f"Total pyc: {len(idx)}")
print(f"Status: {stats}")

ok_list = [e for e in idx if e['decompile_status'] == 'ok']
not_ok = [e for e in idx if e['decompile_status'] != 'ok']
print(f"OK: {len(ok_list)} ({100*len(ok_list)/len(idx):.2f}%)")
print(f"Not-OK: {len(not_ok)}")

# Calculate cumulative match rate
total_funcs = 0
matched_funcs = 0
for e in idx:
    fc = e.get('function_count', 0)
    mr = e.get('bytecode_match_rate', 0.0)
    if fc > 0:
        total_funcs += fc
        matched_funcs += int(fc * mr)
if total_funcs > 0:
    print(f"Cumulative match rate: {matched_funcs}/{total_funcs} = {100*matched_funcs/total_funcs:.2f}%")

# Show failed ones first
failed = [e for e in not_ok if e['decompile_status'] == 'failed']
print(f"\nFailed ({len(failed)}):")
for e in failed[:10]:
    short = e['path'].replace('\\', '/').split('site-packages/')[1] if 'site-packages/' in e['path'].replace('\\', '/') else e['path']
    print(f"  {short} | rate={e.get('bytecode_match_rate', 0)} | round={e.get('last_tested_round', 0)}")

# Show partial ones sorted by match rate ascending
partial = [e for e in not_ok if e['decompile_status'] == 'partial']
partial.sort(key=lambda x: x.get('bytecode_match_rate', 0))
print(f"\nPartial ({len(partial)}), lowest 10:")
for e in partial[:10]:
    short = e['path'].replace('\\', '/').split('site-packages/')[1] if 'site-packages/' in e['path'].replace('\\', '/') else e['path']
    print(f"  {short} | rate={e.get('bytecode_match_rate', 0)} | round={e.get('last_tested_round', 0)}")

# Show pending ones
pending = [e for e in not_ok if e['decompile_status'] == 'pending']
print(f"\nPending ({len(pending)}), first 10:")
for e in pending[:10]:
    short = e['path'].replace('\\', '/').split('site-packages/')[1] if 'site-packages/' in e['path'].replace('\\', '/') else e['path']
    print(f"  {short} | round={e.get('last_tested_round', 0)}")
