"""Round 45 index audit: totals + per-entry drift against the Round-44 landed baseline."""
import io
import json
import sys

REPO = r'F:\Downloads\pythoncdc-main'
sys.stdout.reconfigure(encoding='utf-8')
idx = json.load(io.open(REPO + '/pyc_index.json', encoding='utf-8'))
assert len(idx) == 402, len(idx)


def norm(p):
    return p.replace('\\', '/').replace('F:/Downloads/pythoncdc-main/', '')


base = {}
for l in io.open('D:/Temp/r43gate/g4_r44p12.jsonl', encoding='utf-8'):
    if l.strip():
        r = json.loads(l)
        base[norm(r['path'])] = r

tot = mat = 0
drift = []
rounds = {}
statuses = {}
for e in idx:
    k = norm(e['path'])
    tot += e['function_count']
    mat += e['matched_functions']
    rounds[e.get('last_tested_round')] = rounds.get(e.get('last_tested_round'), 0) + 1
    statuses[e['status']] = statuses.get(e['status'], 0) + 1
    b = base.get(k)
    if b is None:
        drift.append(('NO-BASELINE', k, None, e['matched_functions']))
    elif b['matched_functions'] != e['matched_functions'] or b['total_functions'] != e['function_count']:
        drift.append(('CHANGED', k, '%d/%d' % (b['matched_functions'], b['total_functions']),
                      '%d/%d' % (e['matched_functions'], e['function_count'])))
print('entries=%d  function_count=%d  matched=%d  rate=%.2f%%' % (len(idx), tot, mat, 100.0 * mat / tot))
print('last_tested_round histogram:', rounds)
print('status histogram:', statuses)
print('drift vs Round-44 landed baseline: %d' % len(drift))
for d in drift:
    print('   ', d)
assert tot == 5746, tot
print('OK totals match the frozen function_count 5746')
