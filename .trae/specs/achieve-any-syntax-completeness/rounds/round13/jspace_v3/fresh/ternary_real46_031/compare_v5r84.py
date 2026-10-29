# Compare current-tree J-space verdicts (v5r84 shards) against the v5r79 baseline.
import json, sys
F = r'.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh'

def load_map(paths):
    m = {}
    for p in paths:
        d = json.load(open(p, encoding='utf-8'))
        for r in d['records']:
            m[r['entry_id']] = (r.get('c4', {}).get('verdict'), r.get('status'))
    return m

base = load_map([F + '/semantic_shard0_v5r79.json',
                 F + '/semantic_shard1_v5r79.json',
                 F + '/semantic_shard2_v5r79.json'])
new = load_map([F + '/semantic_shard0_v5r84.json',
                F + '/semantic_shard1_v5r84.json',
                F + '/semantic_shard2_v5r84.json'])

print('baseline entries', len(base), 'new entries', len(new))

from collections import Counter
def hist(m):
    return Counter(v for v, _ in m.values())
print('baseline(v5r79) verdicts', dict(hist(base)))
print('new     (v5r84) verdicts', dict(hist(new)))

changes = []
for eid, (bv, _) in base.items():
    nv = new.get(eid, (None,))[0]
    if nv != bv:
        changes.append((eid, bv, nv))

regress = [(e, b, n) for e, b, n in changes if b == 'EQUAL' and n != 'EQUAL']
improve = [(e, b, n) for e, b, n in changes if b != 'EQUAL' and n == 'EQUAL']
other   = [(e, b, n) for e, b, n in changes if (b == 'EQUAL') == (n == 'EQUAL')]
print()
print('total verdict changes:', len(changes))
print('REGRESSION (EQUAL -> non-EQUAL):', len(regress))
for e, b, n in regress[:60]:
    print('   REGRESS', e, b, '->', n)
print('IMPROVEMENT (non-EQUAL -> EQUAL):', len(improve))
for e, b, n in improve[:60]:
    print('   IMPROVE', e, b, '->', n)
print('other changes (non-EQUAL <-> non-EQUAL):', len(other))
for e, b, n in other[:60]:
    print('   OTHER', e, b, '->', n)

be = sum(1 for v, _ in base.values() if v == 'EQUAL')
ne = sum(1 for v, _ in new.values() if v == 'EQUAL')
print()
print(f'EQUAL count baseline={be} new={ne} delta={ne-be}')
