#!/usr/bin/env python3
"""Check for regressions in pyc_index.json."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, 'pyc_index.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

regressions = []
for entry in data:
    history = entry.get('history', [])
    if len(history) >= 2:
        last = history[-1]
        prev = history[-2]
        prev_rate = prev.get('match_rate', 0)
        last_rate = last.get('match_rate', 0)
        if prev_rate == 100.0 and last_rate < 100.0:
            regressions.append({
                'path': entry['path'],
                'prev_rate': prev_rate,
                'last_rate': last_rate,
                'mismatches': last.get('mismatches', []),
            })

if regressions:
    print(f"Found {len(regressions)} regressions:")
    for r in regressions:
        print(f"  {r['path']}: {r['prev_rate']}% -> {r['last_rate']}%")
        for m in r['mismatches'][:3]:
            print(f"    {m}")
else:
    print("No regressions found!")

# Also show improvements
improvements = []
for entry in data:
    history = entry.get('history', [])
    if len(history) >= 2:
        last = history[-1]
        prev = history[-2]
        prev_rate = prev.get('match_rate', 0)
        last_rate = last.get('match_rate', 0)
        if prev_rate < 100.0 and last_rate == 100.0:
            improvements.append({
                'path': entry['path'],
                'prev_rate': prev_rate,
                'last_rate': last_rate,
            })

if improvements:
    print(f"\nFound {len(improvements)} improvements to 100%:")
    for imp in improvements:
        print(f"  {imp['path']}: {imp['prev_rate']}% -> {imp['last_rate']}%")
