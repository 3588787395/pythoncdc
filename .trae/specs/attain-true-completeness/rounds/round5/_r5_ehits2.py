import io
import json
import os

HERE = r'F:\Downloads\pythoncdc-main\.trae\specs\attain-true-completeness\rounds\round5'

def dump(path, tag):
    d = json.load(io.open(path, encoding='utf-8'))
    rows = d.get('rows', [])
    print('== %s rows=%d keys=%s' % (tag, len(rows), sorted(rows[0].keys()) if rows else []))
    for row in rows:
        st = row.get('status')
        if st and st != 'success':
            print(json.dumps(row, ensure_ascii=False)[:1500])

for i in (1, 6, 7):
    dump(os.path.join(HERE, 'shard%d_report_new.json' % i), 'shard%d' % i)
dump(os.path.join(HERE, 'small34_report_new.json'), 'small34')
