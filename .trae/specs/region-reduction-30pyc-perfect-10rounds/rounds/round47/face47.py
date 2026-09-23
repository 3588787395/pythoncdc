"""sha-change face between two G4 jsonl sides (a=landed baseline, b=arm)."""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
A, B = sys.argv[1], sys.argv[2]


def load(p):
    d = {}
    for line in open(p, encoding='utf-8'):
        line = line.strip()
        if line:
            r = json.loads(line)
            d[r['path']] = r
    return d


a, b = load(A), load(B)
print('a rows %d b rows %d missing-in-a %d' % (len(a), len(b), len([k for k in b if k not in a])))
ch = [k for k in sorted(b) if k in a and a[k]['sha'] != b[k]['sha']]
print('sha-changed products = %d' % len(ch))
up = dn = 0
for k in ch:
    print('   %s %s -> %s' % (k.replace('F:/Downloads/pythoncdc-main/site-packages/', ''),
                              a[k]['matched_functions'], b[k]['matched_functions']))
    up += max(0, b[k]['matched_functions'] - a[k]['matched_functions'])
    dn += max(0, a[k]['matched_functions'] - b[k]['matched_functions'])
print('matched_functions gained=%d lost=%d' % (up, dn))
open(r'D:/Temp/r47mine/changed47a.txt', 'w', encoding='utf-8', newline='\n').write('\n'.join(ch) + '\n')
