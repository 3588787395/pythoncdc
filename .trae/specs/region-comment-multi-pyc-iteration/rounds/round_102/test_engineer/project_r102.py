#!/usr/bin/env python3
"""R102 全局推算精确计算."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
prog = json.loads((HERE / 'progress.json').read_text(encoding='utf-8'))
idx = {e['path']: e for e in json.loads(
    (HERE.parents[5] / 'pyc_index.json').read_text(encoding='utf-8'))}
res = prog['results']

tot_f = mat_f = 0
ok = part = fail = 0
for e in idx.values():
    if e.get('last_tested_round', 0) > 0:
        fc = e.get('function_count', 0)
        r = e.get('bytecode_match_rate', 0.0)
        tot_f += fc
        mat_f += int(round(fc * r))
        st = e.get('decompile_status')
        ok += st == 'ok'
        part += st == 'partial'
        fail += st == 'failed'

print(f'index baseline: ok={ok} partial={part} failed={fail} '
      f'funcs={tot_f} matched={mat_f} rate={mat_f / tot_f:.4f}')

upgrades = [(p, r) for p, r in res.items()
            if r['index_status'] == 'partial' and r.get('match_rate') == 1.0]
proj_mat = mat_f
for p, r in upgrades:
    e = idx[p]
    old = int(round(e.get('function_count', 0) * e.get('bytecode_match_rate', 0.0)))
    new = int(round(r['total_functions']))
    proj_mat += new - old
    print(f'upgrade {p.split("site-packages/")[-1]}: '
          f'contrib {old} -> {new} (+{new - old})')
print(f'scenario A (upgrade only): ok={ok + len(upgrades)} '
      f'partial={part - len(upgrades)} matched={proj_mat} '
      f'rate={proj_mat / tot_f:.4f}')

# scenario B: 再把 data_proxy/cache_storage 按实测重录基线
for p in ['F:/Downloads/pythoncdc-main/site-packages/IQEngine/data/data_proxy.pyc',
          'F:/Downloads/pythoncdc-main/site-packages/IQEngine/utils/cache_storage.pyc']:
    e = idx[p]
    old = int(round(e.get('function_count', 0) * e.get('bytecode_match_rate', 0.0)))
    new = res[p]['matched_functions']
    proj_mat += new - old
    print(f'rebaseline {p.split("site-packages/")[-1]}: '
          f'contrib {old} -> {new} ({new - old:+d})')
print(f'scenario B (A + rebaseline 2 stale-ok): matched={proj_mat} '
      f'rate={proj_mat / tot_f:.4f} (status: ok={ok + len(upgrades) - 2} '
      f'partial={part - len(upgrades) + 2})')
