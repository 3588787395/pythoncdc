# -*- coding: utf-8 -*-
"""Write README.md for each test_repros/round68_diag* witness folder (repo docs, zh-CN)."""
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
GATE = r'D:\Temp\opencode\r68gate\center'
sys.stdout.reconfigure(encoding='utf-8')


def load(f):
    d = {}
    for l in io.open(f, encoding='utf-8'):
        if l.strip():
            r = json.loads(l)
            d[r['path'].replace('\\', '/')] = r
    return d


A = load(GATE + '/dump/repro68_prev.jsonl')
B = load(GATE + '/dump/repro68_landed.jsonl')

BATCH = {
    'round68_diag1': ('diag1', 'B1'),
    'round68_diag3': ('diag3', 'B2'),
    'round68_diag4': ('diag4', 'B3'),
    'round68_diag5': ('diag5', 'B4'),
    'round68_diag6': ('diag6', 'B5'),
}
SPEC = {
    'round68_diag1': '`cand_r68_b1.json`（region_analyzer 3 edit，[R68-B]/[R68-C·循环豁免收紧]/[R68-E·merge 收集的剪枝守卫]）',
    'round68_diag3': '`cand_r68b2_andchain.json`（analyzer 1 edit，[R68-b2 and-chain]）+ `cand_r68b2_final_gen.json`（generator 3 edit，[R68-b2 cell-swap]×2）',
    'round68_diag4': '`cand_r68b3_combo.json`（generator 4 edit，[R68-b3 修复]×2 / [R68-D4-ORCHAIN-TAIL] / [R68-diag3 C3]）',
    'round68_diag5': '`cand_r68_wizapib.json`（analyzer 2 edit，[R68-diag5]×2）',
    'round68_diag6': '`cand_r68b5_initc.json`（generator 4 edit，[R68-diag6/b5 init-if] / [R68-diag6]×2 / [R68-diag6/b5]）',
}
CONSUME = {
    'round68_diag1': '消费者 `matcher::match` 官方 16/17 → 17/17（全清）',
    'round68_diag3': '消费者 `klinedata` 42→43/45、`scheduler` 44→45/45（全清）',
    'round68_diag4': '消费者 `trade_info_utils` 38→39/40、`logger` 29→30/30（全清）',
    'round68_diag5': '消费者 `wizard_quant_api` 52→53/53（全清）、`api_base::get_history_df` [1742,1740,14,1263] → [1742,1742,11,89]',
    'round68_diag6': '消费者 `flyAccount` 21→23/23（全清）',
}


def cell(r):
    if r is None:
        return 'NO-RECORD'
    if r.get('error'):
        return 'ERR ' + r['error'][:40]
    return '%d/%d bad=%d' % (r['matched_functions'], r['total_functions'], len(r['mism'] or []))


for d in sorted(os.listdir(REPO + '/test_repros')):
    if not d.startswith('round68_diag'):
        continue
    ws, lab = BATCH[d]
    files = sorted(p for p in os.listdir(REPO + '/test_repros/' + d) if p.endswith('.pyc'))
    out = ['# %s' % d, '',
           '来源 `D:/Temp/opencode/r68gate/%s`（Round 68 批次 %s）；采纳 spec：%s。'
           % (ws, lab, SPEC[d]),
           '%s。判定臂：`prev`（R67 HEAD 字节）→ `landed`（R68 落地字节），本批 **REGRESSION=0**。'
           % CONSUME[d],
           '',
           '| 见证 | prev → landed |', '|---|---|']
    for f in files:
        key = [p for p in A if p.endswith('/' + d + '/' + f)]
        if not key:
            continue
        k = key[0]
        out.append('| `%s` | %s → %s |' % (f, cell(A[k]), cell(B.get(k))))
    out += ['', '完整诊断与被拒候选见归档 `rounds/round68/batches/`；'
                '`.pyc` 本机编译生成，仓库只入库 `.py`（`.gitignore` 忽略 `*.pyc`）。', '']
    io.open(REPO + '/test_repros/' + d + '/README.md', 'w', encoding='utf-8',
            newline='\r\n').write('\n'.join(out))
    print('wrote %s/README.md  (%d 见证)' % (d, len(files)))
