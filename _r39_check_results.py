import json

with open('pyc_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for entry in data:
    path = entry.get('path', '')
    if 'live_future_position' in path:
        print(f"Path: {path}")
        print(f"Status: {entry.get('decompile_status')}")
        print(f"Match rate: {entry.get('bytecode_match_rate')}")
        print(f"Matched: {entry.get('matched_functions')}/{entry.get('total_functions')}")
        mismatches = entry.get('mismatches', [])
        if mismatches:
            print(f"Mismatches ({len(mismatches)}):")
            for m in mismatches[:10]:
                print(f"  {m.get('name')}: true_diffs={m.get('true_diffs')}, jump_diffs={m.get('jump_diffs')}")
        break

print()
for entry in data:
    path = entry.get('path', '')
    if 'engine/engine' in path and path.endswith('.pyc'):
        print(f"Path: {path}")
        print(f"Status: {entry.get('decompile_status')}")
        print(f"Match rate: {entry.get('bytecode_match_rate')}")
        print(f"Matched: {entry.get('matched_functions')}/{entry.get('total_functions')}")
        mismatches = entry.get('mismatches', [])
        if mismatches:
            print(f"Mismatches ({len(mismatches)}):")
            for m in mismatches[:10]:
                print(f"  {m.get('name')}: true_diffs={m.get('true_diffs')}, jump_diffs={m.get('jump_diffs')}")
        break
