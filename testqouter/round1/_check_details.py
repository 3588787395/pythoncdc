import json
with open('test_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for name in ['test_l01_for_break', 'test_l02_for_continue', 'test_l04_while_break', 'test_l05_while_continue']:
    d = data['details'].get(name, {})
    print(f'=== {name}: {d.get("status", "NOT FOUND")} ===')
    steps = d.get('steps', {})
    bc = steps.get('bytecode_compare', {})
    if bc:
        tds = bc.get('true_diffs', [])
        jds = bc.get('jump_diffs', [])
        print(f'  true_diffs: {len(tds)}, jump_diffs: {len(jds)}')
        for td in tds[:5]:
            print(f'    {td}')
    sem = steps.get('semantic_test', {})
    if sem:
        mismatches = sem.get('mismatches', [])
        print(f'  semantic mismatches: {len(mismatches)}')
        for m in mismatches[:3]:
            print(f'    {m}')
