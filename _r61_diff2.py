#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def parse_verify(filepath):
    results = {}
    current_path = None
    with open(filepath, 'rb') as f:
        for raw_line in f:
            line = raw_line.decode('utf-8', errors='replace').strip()
            m = re.match(r'\[\d+/\d+\]\s+(.+\.pyc)', line)
            if m:
                current_path = m.group(1).strip()
            elif current_path:
                m2 = re.search(r'(\d+)\s+funcs,\s+(\d+)\s+matched', line)
                if m2:
                    results[current_path] = {
                        'total': int(m2.group(1)),
                        'matched': int(m2.group(2)),
                        'status': 'partial' if 'PARTIAL' in line else 'ok'
                    }
                    current_path = None
    return results

r60 = parse_verify('_r60_full_verify.txt')
r61 = parse_verify('_r61_full_verify.txt')

print(f'R60: {len(r60)} files, {sum(r["matched"] for r in r60.values())} matched')
print(f'R61: {len(r61)} files, {sum(r["matched"] for r in r61.values())} matched')

all_paths = set(r60.keys()) | set(r61.keys())
for path in sorted(all_paths):
    r0 = r60.get(path)
    r1 = r61.get(path)
    short = path.replace('F:/Downloads/pythoncdc-main/site-packages/', '')
    if r0 and r1:
        if r0['matched'] != r1['matched']:
            delta = r1['matched'] - r0['matched']
            tag = 'IMPROVE' if delta > 0 else 'REGRESS'
            print(f'{tag} {short}: {r0["matched"]}/{r0["total"]} -> {r1["matched"]}/{r1["total"]} ({delta:+d})')
    elif r0 and not r1:
        print(f'OK_NOW {short}: {r0["matched"]}/{r0["total"]} -> 100%')
    elif r1 and not r0:
        print(f'NEW_PARTIAL {short}: was OK -> {r1["matched"]}/{r1["total"]}')
