import io
import json
import os
import shutil

SRC = r'.trae\specs\region-reduction-v3-full-corpus-100pct-10rounds\rounds\round42\after'
DST = r'.trae\specs\adversarial-complete-forms-v2-10rounds\rounds\round9\baseline42'
OLD = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main'
NEW = 'F:/Downloads/pythoncdc-main'

os.makedirs(DST, exist_ok=True)
for i in range(8):
    name = 'shard%d_report.json' % i
    src = os.path.join(SRC, name)
    raw = io.open(src, encoding='utf-8').read()
    n = raw.count(OLD)
    conv = raw.replace(OLD, NEW)
    out_p = os.path.join(DST, name)
    with io.open(out_p, 'w', encoding='utf-8') as f:
        f.write(conv)
    d = json.loads(conv)
    print(name, 'replaced', n, 'status', d['files_by_status'],
          'units', d['units_success'], '/', d['units_total'])
print('done')
