#!/usr/bin/env python3
"""R102 深挖：疑似回归双口径对比 + 关键条目明细."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
prog = json.loads((HERE / 'progress.json').read_text(encoding='utf-8'))
idx = {e['path']: e for e in json.loads(
    (HERE.parents[5] / 'pyc_index.json').read_text(encoding='utf-8'))}
res = prog['results']

print('=== B-list: dual-denominator comparison ===')
for p, r in sorted(res.items()):
    if r['index_status'] != 'partial':
        continue
    e = idx[p]
    ir, ifc = e.get('bytecode_match_rate', 0), e.get('function_count', 0)
    nt, nmat = r.get('total_functions', 0), r.get('matched_functions', 0)
    d_new = round(ir * nt) - nmat
    d_idx = round(ir * ifc) - nmat
    if d_new >= 1:
        rel = p.split('site-packages/')[-1]
        print(f'{rel:68s} ltr={e.get("last_tested_round"):>3} '
              f'idx(fc={ifc},r={ir:.4f}) new(total={nt},m={nmat},r={r["match_rate"]:.4f}) '
              f'd_idxfc={d_idx:>3} d_newtot={d_new:>3}')

print()
print('=== C-list ok regressions: full index record ===')
for p in ['F:/Downloads/pythoncdc-main/site-packages/IQEngine/data/data_proxy.pyc',
          'F:/Downloads/pythoncdc-main/site-packages/IQEngine/utils/cache_storage.pyc']:
    e = idx[p]
    print(p.split('site-packages/')[-1], '->', json.dumps(e, ensure_ascii=False))

print()
print('=== upgrade candidates: full index record ===')
for p, r in sorted(res.items()):
    if r['index_status'] == 'partial' and r.get('match_rate') == 1.0:
        e = idx[p]
        print(r['pyc'].split('site-packages/')[-1],
              'ltr=', e.get('last_tested_round'),
              'idx_rate=', e.get('bytecode_match_rate'))

print()
print('=== top nomination candidates: ALL mismatches detail ===')
for key in ['IQCommon/const.pyc',
            'IQEngine/plugins/plugin_fly_data_source/fly_data_source.pyc',
            'IQEngine/plugins/plugin_system_accounts/position_model/future_position.pyc']:
    for p, r in res.items():
        if r['index_status'] == 'partial' and p.endswith(key):
            print(f"--- {key}: total={r['total_functions']} matched={r['matched_functions']}")
            for m in r.get('mismatches', []):
                print('   ', json.dumps(m, ensure_ascii=False)[:400])

print()
print('=== ok-sample list (30) with paths & rounds ===')
for p, r in sorted(res.items()):
    if r['index_status'] == 'ok':
        print(f"{p.split('site-packages/')[-1]:70s} ltr={idx[p].get('last_tested_round'):>3} "
              f"measured_status={r.get('status')} rate={r.get('match_rate')}")
