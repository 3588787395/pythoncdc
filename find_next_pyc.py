import json

with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find files that were tested in round 19 or earlier and are not 'ok' status
pending = [e for e in data if e.get('decompile_status') != 'ok' and e.get('last_tested_round', 0) <= 19]
sorted_pending = sorted(pending, key=lambda x: x['path'])

print(f'Found {len(sorted_pending)} candidates for R20')
print('\nFirst 20 candidates:')
for i, e in enumerate(sorted_pending[:20]):
    status = e.get('decompile_status', 'unknown')
    round_num = e.get('last_tested_round', 'never')
    func_count = e.get('function_count', 0)
    path = e['path']
    print(f'{i+1}. {path} - {func_count} functions - status: {status} - round: {round_num}')

# Find medium-small files (≤30 functions) from the candidates
medium_small = [e for e in sorted_pending if e.get('function_count', 0) <= 30]
print(f'\nMedium-small candidates (≤30 functions): {len(medium_small)}')
for i, e in enumerate(medium_small[:10]):
    status = e.get('decompile_status', 'unknown')
    round_num = e.get('last_tested_round', 'never')
    func_count = e.get('function_count', 0)
    path = e['path']
    print(f'{i+1}. {path} - {func_count} functions - status: {status} - round: {round_num}')

if medium_small:
    path = medium_small[0]['path']
    func_count = medium_small[0].get('function_count', 0)
    print(f'\n✓ Selected: {path} ({func_count} functions)')
