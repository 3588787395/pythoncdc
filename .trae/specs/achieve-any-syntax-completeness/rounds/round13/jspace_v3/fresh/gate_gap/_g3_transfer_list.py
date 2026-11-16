# List the 29 entries transferred out of covered_5tuple (R7-only DIFFERENT).
import collections
import json

COV = 'D:/temp/opencode/cl_layout/gap/g3gap/coverage_g3gap.json'
EV = 'D:/temp/opencode/cl_layout/gap/g3fix/semantic_v3m_b275_g3fix_merged.json'
OUT = 'D:/temp/opencode/cl_layout/gap/g3gap/r7_transfer.json'

cov = json.load(open(COV, encoding='utf-8'))
ev = {r['entry_id']: r for r in json.load(open(EV, encoding='utf-8'))['records']}
rows = cov['r7_only_different']
out = []
for index, row in enumerate(rows, 1):
    record = ev.get(row['id'], {})
    c4 = record.get('c4', {})
    out.append({
        'n': index, 'id': row['id'], 'form': row['form'], 'host': row['host'],
        'depth': row['depth'], 'variant': row['variant'], 'verdict': row['verdict'],
        'dimensions': c4.get('diffs'),
        'diff_paths': c4.get('diff_paths') or [],
        'n_diff_paths': len(c4.get('diff_paths') or []),
    })
forms = collections.Counter(item['form'] for item in out)
shapes = collections.Counter(
    'nested_co_code' if any('.co_code' in p for p in item['diff_paths'])
    else 'nested_co_consts_only' for item in out)
payload = {'total': len(out), 'forms': dict(forms), 'shapes': dict(shapes),
           'checked_5tuple_before': 1180, 'checked_5tuple_after': cov['totals']['covered_5tuple'],
           'green': cov['totals']['green'], 'entries': out}
json.dump(payload, open(OUT, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(json.dumps({k: payload[k] for k in ('total', 'forms', 'shapes', 'checked_5tuple_before',
                                          'checked_5tuple_after', 'green')}, ensure_ascii=False,
                 indent=1))
for item in out[:20]:
    print('%2d %-18s %-10s %s' % (item['n'], item['id'], item['form'],
                                  '; '.join(item['diff_paths'][:2])))
