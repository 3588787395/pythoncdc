#!/usr/bin/env python3
"""Compare R60 and R61 batch verification results"""
import re

def parse_verify(filepath):
    results = {}
    current_path = None
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            # Match: [1/153] F:/path/file.pyc
            m = re.match(r'\s*\[\d+/\d+\]\s+(.+\.pyc)', line)
            if m:
                current_path = m.group(1).strip()
            elif current_path:
                if 'PARTIAL:' in line:
                    m2 = re.search(r'(\d+)\s+funcs,\s+(\d+)\s+matched', line)
                    if m2:
                        results[current_path] = {'total': int(m2.group(1)), 'matched': int(m2.group(2)), 'status': 'partial'}
                        current_path = None
                elif 'OK:' in line:
                    m2 = re.search(r'(\d+)/(\d+)', line)
                    if m2:
                        results[current_path] = {'total': int(m2.group(2)), 'matched': int(m2.group(1)), 'status': 'ok'}
                        current_path = None
    return results

r60 = parse_verify('_r60_full_verify.txt')
r61 = parse_verify('_r61_full_verify.txt')

print(f"R60: {len(r60)} files, {sum(r['matched'] for r in r60.values())} matched")
print(f"R61: {len(r61)} files, {sum(r['matched'] for r in r61.values())} matched")

all_paths = set(r60.keys()) | set(r61.keys())
improved = []
regressed = []

for path in all_paths:
    r0 = r60.get(path)
    r1 = r61.get(path)
    short = path.replace('F:/Downloads/pythoncdc-main/site-packages/', '').replace('F:\\Downloads\\pythoncdc-main\\site-packages\\', '')
    
    if r0 and r1:
        if r0['matched'] != r1['matched']:
            delta = r1['matched'] - r0['matched']
            if delta > 0:
                improved.append((short, delta, r0, r1))
            else:
                regressed.append((short, delta, r0, r1))
    elif r0 and not r1:
        # File was in R60 partial but not in R61 - became OK
        improved.append((short, r0['total'] - r0['matched'], r0, None))
    elif r1 and not r0:
        # File is new in R61 - was OK in R60 but now partial
        regressed.append((short, -r1['matched'], None, r1))

print(f"\n=== Improved ({len(improved)}) ===")
for short, delta, r0, r1 in sorted(improved, key=lambda x: -x[1]):
    if r1 is None:
        print(f"  {short}: {r0['matched']}/{r0['total']} -> 100% OK")
    else:
        print(f"  {short}: {r0['matched']}/{r0['total']} -> {r1['matched']}/{r1['total']} ({delta:+d})")

print(f"\n=== Regressed ({len(regressed)}) ===")
for short, delta, r0, r1 in sorted(regressed, key=lambda x: x[1]):
    if r0 is None:
        print(f"  {short}: was OK -> {r1['matched']}/{r1['total']} ({delta:+d})")
    else:
        print(f"  {short}: {r0['matched']}/{r0['total']} -> {r1['matched']}/{r1['total']} ({delta:+d})")
