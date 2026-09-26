# -*- coding: utf-8 -*-
"""Round 72 prep: build filecat.json (all 47 mandated-failure files, R71 reading)
and targets.md (batch plan) in D:/Temp/opencode/r72gate.  Read-only w.r.t. the repo."""
import io
import json
import os
import sys
import collections

sys.stdout.reconfigure(encoding='utf-8')
RT = r'D:/Temp/opencode/r72gate'
G3 = r'D:/Temp/opencode/r71gate/center/logs/G3v_pycverify_r71.json'
REPO = r'F:/Downloads/pythoncdc-main'

g = json.load(io.open(G3, encoding='utf-8'))
ix = json.load(io.open(os.path.join(REPO, 'pyc_index.json'), encoding='utf-8'))
ents = ix['entries'] if isinstance(ix, dict) else ix
off = {}
for e in ents:
    rel = e['path'].replace('\\', '/').split('site-packages/')[-1]
    off[rel] = e

cat = []
for r in g['rows']:
    if r['status'] == 'success':
        continue
    rel = r['pyc'].replace('\\', '/').split('site-packages/')[-1]
    fails = [(f.get('name') if isinstance(f, dict) else str(f)) for f in (r.get('failures') or [])]
    kinds = collections.Counter()
    for s in fails:
        if 'Failure:' in s:
            kinds[s.split('Failure:', 1)[1].strip()] += 1
        elif 'instruction offset' in s:
            kinds['Different bytecode'] += 1
        else:
            kinds[s] += 1
    e = off.get(rel, {})
    cat.append({
        'file': rel,
        'pyc': r['pyc'],
        'official_status': e.get('decompile_status'),
        'official': '%s/%s' % (e.get('matched_functions'), e.get('function_count')),
        'pylingual': '%s/%s' % (r['units_success'], r['units_total']),
        'units_failed': len(fails),
        'cats': dict(kinds),
        'cf': kinds.get('Different control flow', 0),
        'failures': fails,
    })
cat.sort(key=lambda x: (-x['units_failed'], x['file']))
io.open(os.path.join(RT, 'filecat.json'), 'w', encoding='utf-8', newline='\n').write(
    json.dumps(cat, ensure_ascii=False, indent=1))

BATCH = {
    'diag1': ('只读诊断：头部 cf 聚类 + 最小复现 + 三要素提案',
              ['IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc',
               'fly/data/quote.pyc',
               'IQEngine/plugins/plugin_system_simulation/broker.pyc',
               'IQCommon/util/trade_info_utils.pyc',
               'IQData/plugins/plugin_system_realquote/real_quote.pyc',
               'IQCommon/api/klinedata.pyc',
               'IQEngine/core/bar.pyc',
               'IQCommon/strategy/wizard_quant_api.pyc',
               'IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc',
               'IQCommon/data/finance.pyc']),
    'fix1': ('候选 spec：genexpr/listcomp Different bytecode 族（comprehension_generator）',
             ['IQEngine/plugins/plugin_system_accounts/position_model/future_position.pyc',
              'IQEngine/plugins/plugin_system_accounts/position_model/live_future_position.pyc',
              'IQEngine/plugins/plugin_system_accounts/position_model/option_position.pyc',
              'IQEngine/data/asset_mixin.pyc']),
    'fix2': ('候选 spec：头部 control-flow 族（broker 7 + 单元长尾同构）',
             ['IQEngine/plugins/plugin_system_simulation/broker.pyc',
              'fly/data/quote.pyc',
              'IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc',
              'fly/data/quotation.pyc']),
}
idx = {c['file']: c for c in cat}
L = ['# Round 72 目标与分批（数据源：round71 G3v mandated ruler，47 支 failure / 85 cf + 12 bytecode）',
     '',
     '头部（units_failed 降序）：']
for c in cat[:16]:
    L.append('- %-72s %2d fail  pylingual %s  official %s  %s'
             % (c['file'], c['units_failed'], c['pylingual'], c['official'],
                dict(c['cats'])))
L.append('')
L.append('单单元长尾 %d 支（cf=1 为主），本轮不逐支攻坚，仅在候选复测中被动覆盖。'
         % sum(1 for c in cat if c['units_failed'] == 1))
L.append('')
for k, (desc, files) in BATCH.items():
    L.append('## %s — %s' % (k, desc))
    for f in files:
        c = idx.get(f)
        if c is None:
            L.append('- %s  (不在 failure 集，仅作对照)' % f)
            continue
        L.append('- %-72s %2d fail  %s' % (f, c['units_failed'], dict(c['cats'])))
        for s in c['failures']:
            L.append('    - %s' % s)
    L.append('')
io.open(os.path.join(RT, 'targets.md'), 'w', encoding='utf-8', newline='\n').write(
    '\n'.join(L) + '\n')
print('filecat.json entries=%d ; targets.md written' % len(cat))
print('batches:', {k: len(v[1]) for k, v in BATCH.items()})
