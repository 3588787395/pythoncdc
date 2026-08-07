#!/usr/bin/env python3
"""Find next pyc files to fix: failed first, then lowest match rate partial."""
import json
from pathlib import Path

index_path = Path(__file__).resolve().parent.parent / 'pyc_index.json'
with open(index_path, 'r', encoding='utf-8') as f:
    entries = json.load(f)

failed = [e for e in entries if e.get('decompile_status') == 'failed']
partial = [e for e in entries if e.get('decompile_status') == 'partial']
ok = [e for e in entries if e.get('decompile_status') == 'ok']
pending = [e for e in entries if e.get('decompile_status') == 'pending']

print(f'Total: {len(entries)}, OK: {len(ok)}, Partial: {len(partial)}, Failed: {len(failed)}, Pending: {len(pending)}')

if failed:
    print('\n=== FAILED ===')
    for e in failed:
        p = e['path'].split('site-packages/')[-1] if 'site-packages/' in e['path'] else e['path']
        print(f'  {p}: rate={e.get("bytecode_match_rate",0):.4f} funcs={e.get("function_count",0)} round={e.get("last_tested_round",0)}')

print('\n=== LOWEST 20 PARTIAL ===')
partial_sorted = sorted(partial, key=lambda e: e.get('bytecode_match_rate', 0))
for e in partial_sorted[:20]:
    p = e['path'].split('site-packages/')[-1] if 'site-packages/' in e['path'] else e['path']
    print(f'  {p}: rate={e.get("bytecode_match_rate",0):.4f} funcs={e.get("function_count",0)} round={e.get("last_tested_round",0)}')
