# rr-v5r114 compare：v5r114 三分片 + 46 sweep 对 v5r113 基线逐案 c4 verdict 对比
# 用法：python compare_v5r114.py [--shard N] [--sweep]
# 输出：逐案变化清单 + 分片汇总 + 需单案复跑的抖动候选清单
import json, sys, os

REPO = 'F:/Downloads/pythoncdc-main'
BASE = REPO + '/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh'
OLD = 'v5r113'
NEW = 'v5r114'


def load(path):
    if not os.path.exists(path):
        return None
    d = json.load(open(path, encoding='utf-8'))
    recs = d['records'] if isinstance(d, dict) and 'records' in d else d
    out = {}
    for x in recs:
        c4 = x.get('c4') or {}
        v = c4.get('verdict') or x.get('status')
        out[x.get('entry_id') or x.get('case_id')] = {
            'verdict': v,
            'sha': (x.get('c3') or {}).get('sha256'),
            'diffs': c4.get('diffs'),
            'note': x.get('note', ''),
        }
    return out


def cmp_shard(i):
    old = load(BASE + '/semantic_shard%d_%s.json' % (i, OLD))
    new = load(BASE + '/semantic_shard%d_%s.json' % (i, NEW))
    if old is None or new is None:
        print('shard%d: MISSING (old=%s new=%s)' % (i, old is not None, new is not None))
        return
    ids = [k for k in new if k in old]
    changes = []
    from collections import Counter
    co, cn = Counter(), Counter()
    for k in ids:
        vo, vn = old[k]['verdict'], new[k]['verdict']
        co[vo] += 1
        cn[vn] += 1
        if vo != vn or (old[k]['sha'] and new[k]['sha'] and old[k]['sha'] != new[k]['sha']):
            changes.append((k, vo, vn, 'sha-diff' if old[k]['sha'] != new[k]['sha'] else 'verdict-only'))
    print('shard%d: %d cases' % (i, len(ids)))
    print('  old:', dict(sorted(co.items())))
    print('  new:', dict(sorted(cn.items())))
    print('  changes: %d' % len(changes))
    for k, vo, vn, why in changes:
        print('    %-22s %-12s -> %-12s %s' % (k, vo, vn, why))
    worse = [c for c in changes if c[2] in ('ERROR', 'INCONCLUSIVE') and c[1] == 'EQUAL']
    print('  worse(EQUAL->ERR):', [c[0] for c in worse])
    return changes


def cmp_sweep():
    old = load(BASE + '/whileyield_break/semantic_46_%s.json' % OLD)
    new = load(BASE + '/argor_mergenop/semantic_46_%s.json' % NEW)
    if old is None or new is None:
        print('sweep: MISSING (old=%s new=%s)' % (old is not None, new is not None))
        return
    ids = [k for k in new if k in old]
    changes = []
    from collections import Counter
    co, cn = Counter(), Counter()
    for k in ids:
        vo, vn = old[k]['verdict'], new[k]['verdict']
        co[vo] += 1
        cn[vn] += 1
        if vo != vn:
            changes.append((k, vo, vn))
    print('sweep46: %d cases' % len(ids))
    print('  old:', dict(sorted(co.items())))
    print('  new:', dict(sorted(cn.items())))
    print('  verdict changes: %d' % len(changes))
    for k, vo, vn in changes:
        print('    %-12s %-10s -> %s' % (k, vo, vn))
    return changes


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--sweep' in args:
        cmp_sweep()
    else:
        shards = [int(a.split('=')[1]) for a in args if a.startswith('--shard=')] or [0, 1, 2]
        for i in shards:
            cmp_shard(i)
