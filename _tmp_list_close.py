#!/usr/bin/env python3
"""List partial pyc files sorted by match rate (highest first - closest to OK)."""
import json
idx = json.load(open('pyc_index.json', 'r', encoding='utf-8'))
partials = [e for e in idx if e.get('decompile_status') == 'partial']
partials.sort(key=lambda e: e.get('bytecode_match_rate', 0), reverse=True)
print(f"Top 30 partial files (highest match rate - closest to OK):")
for e in partials[:30]:
    rate = e.get('bytecode_match_rate', 0)
    path = e.get('path', '?')
    short = path.replace('f:\\Downloads\\pythoncdc-main\\site-packages\\', '')
    short = short.replace('F:/Downloads/pythoncdc-main/site-packages/', '')
    fc = e.get('function_count', 0)
    print(f"  {rate:.4f}  ({fc} fns)  {short}")
