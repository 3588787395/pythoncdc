import json

idx = json.load(open('pyc_index.json', 'r', encoding='utf-8'))
not_ok = [e for e in idx if e['decompile_status'] != 'ok']

# Calculate unmatched functions for each file
for e in not_ok:
    e['unmatched'] = e['function_count'] * (1 - e['bytecode_match_rate'])

# Sort by unmatched count descending (most impactful first)
not_ok.sort(key=lambda x: x['unmatched'], reverse=True)

print("=== Top 20 pyc files by unmatched function count ===")
for e in not_ok[:20]:
    short = e['path'].split('site-packages/')[-1]
    print(f"  {e['unmatched']:6.1f} unmatched  {e['function_count']:3d} funcs  {e['bytecode_match_rate']:.4f}  {e['decompile_status']:8s}  {short}")

print()
print(f"Total unmatched functions: {sum(e['unmatched'] for e in not_ok):.0f}")
print(f"Total not-ok files: {len(not_ok)}")
