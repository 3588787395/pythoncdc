import json
with open('pyc_index.json', 'r', encoding='utf-8') as f:
    index = json.load(f)
for entry in index:
    if entry.get('decompile_status') != 'partial':
        continue
    matched = entry.get('matched_functions', 0)
    total = entry.get('function_count', 0)
    rate = entry.get('bytecode_match_rate', 0)
    if total > 0 and matched >= total:
        p = entry['path'].split('site-packages')[-1]
        print(f"{p}: {matched}/{total} rate={rate}")
