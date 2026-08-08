#!/usr/bin/env python3
"""List partial pyc files sorted by match rate (lowest first)."""
import json, sys
idx = json.load(open('pyc_index.json', 'r', encoding='utf-8'))
partials = [e for e in idx if e.get('decompile_status') == 'partial']
partials.sort(key=lambda e: e.get('bytecode_match_rate', 0))
print(f"Total: {len(idx)}, OK: {sum(1 for e in idx if e.get('decompile_status')=='ok')}, "
      f"Partial: {len(partials)}, Failed: {sum(1 for e in idx if e.get('decompile_status')=='failed')}")
print(f"\nTop 30 partial files (lowest match rate):")
for e in partials[:30]:
    rate = e.get('bytecode_match_rate', 0)
    path = e.get('path', '?')
    # shorten path for display
    short = path.replace('f:\\Downloads\\pythoncdc-main\\site-packages\\', '')
    print(f"  {rate:.4f}  {short}")
