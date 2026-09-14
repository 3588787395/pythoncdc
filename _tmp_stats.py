import json
data = json.load(open('pyc_index.json', 'r', encoding='utf-8'))
partials = [e for e in data if e.get('decompile_status') == 'partial']
partials.sort(key=lambda e: e.get('bytecode_match_rate', 0), reverse=True)
print(f'Partial: {len(partials)}')
for e in partials:
    rate = e.get('bytecode_match_rate', 0)
    matched = e.get('matched_functions', 0)
    total = e.get('function_count', 0)
    path = e.get('path', '')
    print(f'  {rate:.3f} {matched}/{total} {path}')
print()
failed = [e for e in data if e.get('decompile_status') == 'failed']
print(f'Failed: {len(failed)}')
for e in failed:
    path = e.get('path', '')
    error = e.get('error', '')[:100]
    print(f'  {path} error={error}')
