"""Round-closeout residual emitter for the region-reduction campaign.

Why this exists: the campaign's own rule is that when the 10 rounds are exhausted without 100 %,
the report must list the residual as 文件 × 单元 × 违反条款 and must not tune a criterion or
hand-edit a product to buy a reading. Transcribing that table by hand is exactly how a unit gets
silently dropped, so the table is emitted from two sources and *asserts its own coverage*:

  1. the sealed per-shard judge reports in rounds/round<label>/after/shard*_report.json
     (units_success/units_total/status/failures per file), and
  2. the mechanism register rounds/round10/UNITMAP_R10.md, which is grepped per failing unit.

Any failing unit whose name does not appear in the register is printed as UNREGISTERED and the
exit status is 1 — a hole in the table then fails loudly instead of reading as a smaller residual.

Usage: python -X utf8 residual_report.py <label> [<before-label>]
"""
import glob
import json
import os
import re
import sys

# (SPEC/ROOT assigned below) with RESID_ROOT when run elsewhere
# root derives from this file's own location (same fix as tools/kb/*.py: a literal
# absolute path silently measures whichever checkout it names, not the running worktree)
SPEC = os.path.abspath(os.path.join(os.path.dirname(__file__)))
ROOT = os.path.abspath(os.path.join(SPEC, '..', '..', '..'))
if not os.path.isfile(os.path.join(ROOT, 'pycdc.py')):
    sys.exit('[fatal] ROOT 解析错误：%s 下没有 pycdc.py' % ROOT)
REGISTER = os.path.join(SPEC, 'rounds', 'round10', 'UNITMAP_R10.md')


def rows_of(label):
    out = {}
    d = os.path.join(SPEC, 'rounds', 'round%s' % label, 'after')
    files = sorted(glob.glob(os.path.join(d, 'shard*_report.json')))
    if len(files) != 8:
        print('!! %s: %d/8 shard reports present — the gate did not finish, refuse to emit'
              % (label, len(files)))
        sys.exit(2)
    for f in files:
        with open(f, encoding='utf-8') as fh:
            for r in json.load(fh)['rows']:
                out[r['pyc']] = r
    return out


def register_text():
    with open(REGISTER, encoding='utf-8-sig') as fh:
        return fh.read()


def mechanism_for(text, unit, fname):
    """Quote the single most specific register line naming this unit.

    Grep-joining every hit produced multi-hundred-cell prose that broke the markdown table, so:
    prefer a table row ('|'-delimited), then the shortest candidate (the most specific line), and
    escape any remaining pipe characters.
    """
    short = unit.split('.')[-1]
    base = os.path.basename(fname).replace('.pyc', '')
    hits = []
    for line in text.splitlines():
        low = line.lower()
        # a quoted register line must name THIS unit and belong to THIS file, otherwise a
        # generic tail like `<module>` matches another file's row and the table publishes a
        # claim about a different unit
        if (short.lower() in low or unit.lower() in low) and base.lower() in low:
            hits.append(line.strip())
    if not hits:
        return None
    rows = [h for h in hits if h.startswith('|')]
    pick = min(rows or hits, key=len)
    return pick.replace('|', '\\|')[:300]


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else '10'
    before = sys.argv[2] if len(sys.argv) > 2 else None
    rows = rows_of(label)
    text = register_text()
    units_t = sum(r['units_total'] for r in rows.values())
    units_s = sum(r['units_success'] for r in rows.values())
    files_ok = sum(1 for r in rows.values() if r['status'] == 'success')
    failing = {k: v for k, v in rows.items() if v['units_total'] - v['units_success'] > 0}
    print('# 封表时点 %s / label round%s / 数据源 rounds/round%s/after(8 shards)'
          % (re.sub(r'\..*$', '', __import__('time').strftime('%H:%M:%S')), label, label))
    print('单元 %d/%d (%.4f%%)  文件 %d/%d  残余文件 %d 个  残余单元 %d 条'
          % (units_s, units_t, 100.0 * units_s / units_t, files_ok, len(rows),
             len(failing), sum(r['units_total'] - r['units_success'] for r in failing.values())))
    if before:
        b = rows_of(before)
        bu = sum(v['units_success'] for v in b.values())
        bf = sum(1 for v in b.values() if v['status'] == 'success')
        print('对照 round%s：单元 %d -> %d  文件 %d -> %d' % (before, bu, units_s, bf, files_ok))
    unreg = 0
    print()
    print('| 文件 | 单元读数 | 失败单元（完整 qualname） | 台账登记的机制/条款 |')
    print('|---|---|---|---|')
    for path in sorted(failing):
        r = failing[path]
        rel = path.split('site-packages/')[-1]
        for u in r['failures']:
            unit = u.replace('***', '').split(': ')[0]
            mech = mechanism_for(text, unit, rel)
            if mech is None:
                unreg += 1
                mech = '**UNREGISTERED（台账无此单元，须补登再封表）**'
            print('| `%s` | %d/%d | `%s` | %s |' % (rel, r['units_success'], r['units_total'],
                                                    unit, mech))
    print()
    print('UNREGISTERED 行数=%d（应为 0）' % unreg)
    sys.exit(1 if unreg else 0)


if __name__ == '__main__':
    main()
