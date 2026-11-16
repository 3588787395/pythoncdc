# Re-judge the G2b (402 corpus) and G2c (46 real pyc) records with the current
# semantic_diff (new ruler).  C1/C2/C3 are taken from the round9 records and the
# products are the frozen round9 artifacts, so the only variable is the ruler.
import collections
import json
import os
import sys
import time

REPO = 'F:/Downloads/pythoncdc-main'
WORK = 'D:/temp/opencode/cl_layout/gap/g3gap'
SPACES = [
    ('g2b', REPO + '/.trae/specs/attack-completeness-claims/rounds/round9/g2b_402/semantic_402.json'),
    ('g2c', REPO + '/.trae/specs/attack-completeness-claims/rounds/round9/g2c_46/semantic_46.json'),
]


def abspath(value):
    value = (value or '').replace('\\', '/')
    return value if os.path.isabs(value) else os.path.join(REPO, value)


def judge(records, tag, out):
    import semantic_diff as sd
    rows = []
    started = time.time()
    for index, record in enumerate(records, 1):
        eid = record['entry_id']
        old = record.get('c4', {}).get('verdict')
        pyc = abspath(record.get('c2', {}).get('pyc_path'))
        product = abspath(record.get('c3', {}).get('product_path'))
        case = {'case_id': eid, 'original': {'pyc': pyc}, 'product': {'source': product},
                'entrypoint': 'module', 'args': [], 'kwargs': {}, 'timeout_s': 20,
                '_base': REPO}
        try:
            result = sd.compare_case(case)
        except BaseException as exc:
            result = {'status': 'ERROR', 'diffs': [], 'errors': ['%s: %s' % (type(exc).__name__, exc)],
                      'inconclusive': []}
        diffs = result.get('diffs') or []
        dims = [d.get('dimension') for d in diffs if isinstance(d, dict)]
        rows.append({
            'entry_id': eid, 'old_verdict': old, 'new_verdict': result.get('status'),
            'r7_only': bool(dims) and all(d == 'R7' for d in dims),
            'dimensions': dict(collections.Counter(dims)),
            'n_diffs': len(diffs), 'paths': [d.get('path') for d in diffs][:12],
            'errors': (result.get('errors') or [])[:4],
            'inconclusive': (result.get('inconclusive') or [])[:4],
        })
        if index % 25 == 0:
            print('[%s] %d/%d %.0fs' % (tag, index, len(records), time.time() - started), flush=True)
    old_counts = collections.Counter(row['old_verdict'] for row in rows)
    new_counts = collections.Counter(row['new_verdict'] for row in rows)
    flips = [row for row in rows if row['old_verdict'] != row['new_verdict']]
    to_different = [row for row in flips if row['new_verdict'] == 'DIFFERENT']
    payload = {
        'tag': tag, 'records': len(rows), 'old_counts': dict(old_counts),
        'new_counts': dict(new_counts), 'flips': len(flips),
        'flips_to_different': len(to_different),
        'flips_to_different_r7_only': sum(1 for row in to_different if row['r7_only']),
        'new_different_r7_only': sum(1 for row in rows
                                     if row['new_verdict'] == 'DIFFERENT' and row['r7_only']),
        'new_different_with_behavior': sum(1 for row in rows
                                           if row['new_verdict'] == 'DIFFERENT'
                                           and not row['r7_only']),
        'elapsed_s': round(time.time() - started, 1), 'rows': rows,
    }
    json.dump(payload, open(out, 'w', encoding='utf-8', newline='\n'),
              ensure_ascii=False, indent=1)
    print('[%s] old=%s new=%s flips=%d->DIFF=%d' % (
        tag, dict(old_counts), dict(new_counts), len(flips), len(to_different)), flush=True)
    for row in to_different[:40]:
        print('  -> %-18s %s %s' % (row['entry_id'], row['dimensions'], row['paths'][:2]), flush=True)


def main():
    sys.path.insert(0, REPO + '/tools/completeness')
    os.chdir(REPO)
    which = sys.argv[1] if len(sys.argv) > 1 else 'both'
    os.makedirs(WORK, exist_ok=True)
    for tag, path in SPACES:
        if which not in ('both', tag):
            continue
        data = json.load(open(path, encoding='utf-8-sig'))
        judge(data['records'], tag, os.path.join(WORK, 'rejudge_%s.json' % tag))


if __name__ == '__main__':
    main()
