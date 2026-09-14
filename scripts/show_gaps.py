import json
with open('pyc_index.json', 'r', encoding='utf-8') as f:
    entries = json.load(f)
partials = [e for e in entries if e.get('status') == 'partial']
partials.sort(key=lambda e: e.get('function_count', 0) - e.get('matched_functions', 0), reverse=True)
for e in partials[:15]:
    gap = e.get('function_count', 0) - e.get('matched_functions', 0)
    path = e.get('path', '?')
    mf = e.get('matched_functions', 0)
    fc = e.get('function_count', 0)
    rate = e.get('bytecode_match_rate', 0) * 100
    print(path + ': ' + str(mf) + '/' + str(fc) + ' gap=' + str(gap) + ' rate=' + str(round(rate, 1)) + '%')
