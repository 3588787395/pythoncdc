import json

# Read the current pyc_index.json
with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Update backtest.pyc with R20 results
for entry in data:
    if 'backtest/backtest.pyc' in entry['path']:
        entry['last_tested_round'] = 20
        entry['decompile_status'] = 'partial'
        entry['bytecode_match_rate'] = 0.5
        entry['ok_py_generated'] = True
        print(f'Updated {entry[\"path\"]}')
        break

# Calculate new cumulative success rate
verified_count = sum(1 for e in data if e.get('last_tested_round', 0) <= 20)
total_functions = sum(e.get('function_count', 0) for e in data if e.get('last_tested_round', 0) <= 20)
matched_functions = 0

# Estimate matched functions based on match rates
for entry in data:
    if entry.get('last_tested_round', 0) <= 20:
        match_rate = entry.get('bytecode_match_rate', 0.0)
        func_count = entry.get('function_count', 0)
        matched_functions += int(match_rate * func_count)

cumulative_rate = (matched_functions / total_functions * 100) if total_functions > 0 else 0.0

print(f'\\nCumulative success rate after R20: {cumulative_rate:.2f}% ({matched_functions}/{total_functions} matched functions)')

# Write back to pyc_index.json
with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print('\\nUpdated pyc_index.json successfully')
