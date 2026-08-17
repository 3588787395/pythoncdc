#!/usr/bin/env python3
import json
import os

with open('pyc_index.json', 'r', encoding='utf-8') as f:
    index = json.load(f)

partial_files = []
for entry in index:
    if entry['decompile_status'] in ['partial', 'failed']:
        partial_files.append((entry['path'], entry['decompile_status'], entry['bytecode_match_rate']))

print(f"Total partial/failed files: {len(partial_files)}")
print("\nFirst 20 files:")
for path, status, rate in sorted(partial_files)[:20]:
    print(f"{status} {rate:.2%} - {path}")