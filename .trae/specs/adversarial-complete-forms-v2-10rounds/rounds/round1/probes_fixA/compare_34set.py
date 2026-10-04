"""[fixA] 34 小测试集跑批读数 vs failing_index.json 基线对比（回归判定：无 success→failure 位移）。"""
import json
import re

LOG = r'.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_fixA/tmp/34set_run.log'
BASE = r'.trae/specs/adversarial-complete-forms-v2-10rounds/baseline/failing_index.json'

log = open(LOG, encoding='utf-8', errors='replace').read()
blocks = re.split(r'^===== ', log, flags=re.M)[1:]
base = json.load(open(BASE, encoding='utf-8'))
bmap = {}
for e in base:
    key = e['path'].split('pythoncdc-main/')[-1]
    bmap[key] = (e['units_success'], e['units_total'])
total_b_s = total_b_t = total_n_s = total_n_t = 0
regress = []
for blk in blocks:
    lines = blk.strip().splitlines()
    if not lines:
        continue
    path = lines[0].strip()
    if path == 'ALL DONE':
        print('[ALL DONE marker present]')
        continue
    m = re.search(r'matched_functions:\s*(\d+)', blk)
    t = re.search(r'total_functions:\s*(\d+)', blk)
    ms = re.search(r'match_rate:\s*([\d.]+)%', blk)
    if not (m and t):
        print('NO DATA:', path)
        continue
    ns, nt = int(m.group(1)), int(t.group(1))
    key = path.replace('F:/Downloads/pythoncdc-main/', '')
    key = key.replace('\\', '/')
    bs, bt = bmap.get(key, (None, None))
    total_b_s += bs or 0
    total_b_t += bt or 0
    total_n_s += ns
    total_n_t += nt
    flag = ''
    if bs is not None and ns < bs:
        flag = ' <<< REGRESSION'
        regress.append((key, bs, ns))
    name = key.split('/')[-1]
    rate = ms.group(1) if ms else '?'
    print('%-46s base=%s/%s now=%s/%s (%s%%)%s' % (name, bs, bt, ns, nt, rate, flag))
print()
print('TOTAL baseline=%d/%d  now=%d/%d' % (total_b_s, total_b_t, total_n_s, total_n_t))
print('REGRESSIONS:', regress if regress else 'NONE')
