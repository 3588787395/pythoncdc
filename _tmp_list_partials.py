import json
data = json.load(open('pyc_index.json', 'r', encoding='utf-8'))
partials = [d for d in data if d.get('decompile_status') == 'partial']
partials.sort(key=lambda x: (-x.get('bytecode_match_rate', 0), x.get('function_count', 0)))
print(f"Partial files: {len(partials)}")
for d in partials[:10]:
    rate = d.get('bytecode_match_rate', 0)
    fc = d.get('function_count', 0)
    matched = int(fc * rate)
    p = d.get('path', '').replace('F:/Downloads/pythoncdc-main/site-packages/', '')
    print(f"  {rate:.2%} ({matched}/{fc}) - {p}")
