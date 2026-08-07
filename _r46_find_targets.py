import json
entries = json.load(open('pyc_index.json', 'r', encoding='utf-8'))
partials = [e for e in entries if e.get('decompile_status') == 'partial']
partials.sort(key=lambda e: e.get('bytecode_match_rate', 0))
for e in partials[:30]:
    rate = e.get('bytecode_match_rate', 0)
    fc = e.get('function_count', 0)
    path = e.get('path', '')
    print(f"{rate:.2%}  {fc:3d}  {path}")
print(f"\nTotal partial: {len(partials)}")
