import json
with open('pyc_index.json', 'r') as f:
    idx = json.load(f)

failed = [e for e in idx if e['decompile_status'] == 'failed']
print("Failed:")
for e in failed:
    p = e['path'].replace('\\', '/')
    short = p.split('site-packages/')[1] if 'site-packages/' in p else p
    print(f"  {short} | rate={e.get('bytecode_match_rate', 0)} | round={e.get('last_tested_round', 0)}")

partial = [e for e in idx if e['decompile_status'] == 'partial']
partial.sort(key=lambda x: x.get('bytecode_match_rate', 0))
print(f"\nPartial ({len(partial)}), lowest 15:")
for e in partial[:15]:
    p = e['path'].replace('\\', '/')
    short = p.split('site-packages/')[1] if 'site-packages/' in p else p
    print(f"  {short} | rate={e.get('bytecode_match_rate', 0)} | funcs={e.get('function_count', 0)} | round={e.get('last_tested_round', 0)}")
