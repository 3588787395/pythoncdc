import json
with open('test_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
for name in ['test_l01_for_break', 'test_l02_for_continue', 'test_l04_while_break', 'test_l05_while_continue']:
    d = data['details'].get(name, {})
    print(f'{name}: {d.get("status", "NOT FOUND")}')
