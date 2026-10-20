import io
import json
import os

HERE = r'F:\Downloads\pythoncdc-main\.trae\specs\attain-true-completeness\rounds\round5'
for i in range(8):
    p = os.path.join(HERE, 'shard%d_report_new.json' % i)
    d = json.load(io.open(p, encoding='utf-8'))
    print('shard%d units=%s/%s files=%s' % (i, d.get('units_success'), d.get('units_total'),
                                            d.get('files_by_status')))
    for row in d.get('rows', []):
        st = row.get('status')
        if st and st != 'success':
            print('  %s %s units=%s/%s' % (st, row.get('path'), row.get('units_success'),
                                           row.get('units_total')))
            for f in row.get('failures', []):
                print('    - ' + str(f)[:200])
for s in ('small34_report_new.json',):
    d = json.load(io.open(os.path.join(HERE, s), encoding='utf-8'))
    print('%s units=%s/%s files=%s' % (s, d.get('units_success'), d.get('units_total'),
                                       d.get('files_by_status')))
