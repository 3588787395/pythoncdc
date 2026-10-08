"""One-shot round gate driver for the region-reduction campaign (staged to respect the 300s cap).

Stages (run one per invocation; `all` is refused so no single command can exceed 300s):
  regen   - regenerate the 402 corpus products from the CURRENT working-tree code, shard by shard
            (regen_list.py deletes each product before producing it; each shard call is bounded)
  verify  - verify each shard with the sole judge into rounds/round<label>/after/
  report  - compare with the previous round: file-level REGRESSIONS, UNIT_REGRESSIONS,
            and the unit-name movement (fixed / newly failing). No subprocesses: pure JSON.
  checks  - quotation single verify, small34 batch, ruler selfcheck, six pytest suites

Usage: python -X utf8 gate_round.py <label> <before-label> --stage {regen,verify,report,checks}
"""
import argparse
import json
import os
import subprocess
import sys

SPEC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(SPEC, '..', '..', '..'))
SHARDS = 8
LISTDIR = 'D:/Temp/r9main'
TOTAL_FILES = 402


def run(cmd, timeout=250, cwd=ROOT):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=timeout)
    except subprocess.TimeoutExpired:
        return 124, '', 'TIMEOUT after %ds' % timeout
    return p.returncode, (p.stdout or ''), (p.stderr or '')


def rel_list(shard):
    idx = json.load(open(os.path.join(SPEC, 'baseline', 'shards', 'shard%d.json' % shard), encoding='utf-8'))
    path = os.path.join(LISTDIR, 'shard%d_rel.txt' % shard)
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        for e in idx:
            fh.write('site-packages/' + e['rel'] + '\n')
    return path


def after_dir(label):
    d = os.path.join(SPEC, 'rounds', 'round%s' % label, 'after')
    os.makedirs(d, exist_ok=True)
    return d


def load_rows(label):
    rows = {}
    d = os.path.join(SPEC, 'rounds', 'round%s' % label, 'after')
    for f in sorted(os.listdir(d)):
        if not (f.startswith('shard') and f.endswith('_report.json')):
            continue
        for r in json.load(open(os.path.join(d, f), encoding='utf-8'))['rows']:
            rows[r['pyc']] = (r['units_success'], r['units_total'], r['status'],
                              frozenset(x.split(': ')[0].replace('***', '') for x in r.get('failures', [])))
    return rows


def stage_regen(label, budget=240):
    """Regenerate every corpus product from the CURRENT working-tree bytes.

    Each shard needs more wall time than one bounded child allows (measured ~7 s per file, so a
    50-file shard is ~350 s against a 120 s budget), and `regen_list.py` exits rc=3 with
    `BUDGET NEXT=<cursor>`. The previous version of this stage ignored that cursor, so any
    re-invocation restarted the shard from zero and the 402-file regen could never complete.
    Cursors are therefore kept per shard and advanced in-process only: an invocation always
    begins at zero, because re-running the gate after a landing must not reuse products made by
    the previous bytes.
    """
    ok = bad = 0
    for s in range(SHARDS):
        path = rel_list(s)
        cursor, passes = 0, 0
        while True:
            rc, so, se = run([sys.executable, '-X', 'utf8', os.path.join(SPEC, 'regen_list.py'),
                              str(budget), path] + ([str(cursor)] if cursor else []),
                             timeout=budget + 40)
            lines = [l for l in so.splitlines() if l.startswith('REGEN') or l.startswith('BUDGET')]
            for l in lines:
                for tok in l.split():
                    if tok.startswith('ok='):
                        ok += int(tok[3:])
                    elif tok.startswith('bad='):
                        bad += int(tok[4:].rstrip('s'))
            nxt = [tok for l in lines if 'NEXT=' in l for tok in l.split() if tok.startswith('NEXT=')]
            passes += 1
            if rc == 0:
                print('[regen %d] done in %d pass(es) ok=%d bad=%d' % (s, passes, ok, bad))
                break
            if rc == 3 and nxt:
                cursor = int(nxt[-1].split('=')[1])
                print('[regen %d] BUDGET 续跑 cursor=%d (pass %d)' % (s, cursor, passes))
                continue
            print('[regen %d] rc=%d 未预期，停止本分片：%s' % (s, rc, (se or so).strip()[-200:]))
            break
    print('[regen 合计] ok=%d bad=%d（应 ok=%d bad=0）' % (ok, bad, TOTAL_FILES))


def stage_verify(label):
    out = after_dir(label)
    for s in range(SHARDS):
        rc, so, se = run([sys.executable, '-X', 'utf8', 'scripts/pyc_verify.py', 'batch',
                          '--index', os.path.join(SPEC, 'baseline', 'shards', 'shard%d.json' % s),
                          '--json', os.path.join(out, 'shard%d_report.json' % s)], timeout=250)
        agg = {}
        for l in so.splitlines():
            for k in ('units_success', 'units_total'):
                if '"%s"' % k in l:
                    try:
                        agg[k] = int(l.split(':')[1].strip().rstrip(','))
                    except ValueError:
                        pass
        print('[verify %d] rc=%d %s/%s' % (s, rc, agg.get('units_success'), agg.get('units_total')))


def stage_report(label, before):
    b, af = load_rows(before), load_rows(label)
    if set(b) != set(af):
        print('!! 前后文件集合不等：%d vs %d（不可判）' % (len(b), len(af)))
        return
    ub, ua, ut = (sum(v[0] for v in b.values()), sum(v[0] for v in af.values()),
                  sum(v[1] for v in b.values()))
    fb = sum(1 for v in b.values() if v[2] == 'success')
    fa = sum(1 for v in af.values() if v[2] == 'success')
    down = [(k, b[k][0], af[k][0]) for k in b if af[k][0] < b[k][0]]
    up = [(k, b[k][0], af[k][0]) for k in b if af[k][0] > b[k][0]]
    broke = [k for k in b if b[k][2] == 'success' and af[k][2] != 'success']
    ob = {(k, u) for k in b for u in b[k][3]}
    oa = {(k, u) for k in af for u in af[k][3]}
    print('[units] %d/%d -> %d/%d  (%.4f%%)   [files] %d -> %d' %
          (ub, ut, ua, ut, 100.0 * ua / ut, fb, fa))
    print('[gates] 文件级回退=%d  UNIT_REGRESSIONS=%d  新增失败单元=%d  翻正单元=%d' %
          (len(broke), len(down), len(oa - ob), len(ob - oa)))
    for k in broke:
        print('   FILE-BROKE', k.split('site-packages/')[-1])
    for k, x, y in down:
        print('   UNIT-DOWN', k.split('site-packages/')[-1], x, '->', y)
    for k, u in sorted(ob - oa):
        print('   FIXED', k.split('site-packages/')[-1], u)
    for k, u in sorted(oa - ob):
        print('   NEW-FAIL', k.split('site-packages/')[-1], u)
    for k, x, y in up:
        print('   UNIT-UP', k.split('site-packages/')[-1], x, '->', y)


def stage_checks(label):
    rc, so, se = run([sys.executable, '-X', 'utf8', 'scripts/pyc_verify.py', 'single',
                      'site-packages/fly/data/quotation.pyc'], timeout=240)
    got = [l for l in so.splitlines() if 'status=' in l]
    print('[quotation] rc=%d %s' % (rc, got[-1] if got else 'NO STATUS LINE'))
    rc, so, se = run([sys.executable, '-X', 'utf8', 'scripts/pyc_verify.py', 'batch',
                      '--index', os.path.join(SPEC, 'baseline', 'small34_index.json'),
                      '--json', 'D:/Temp/r9main/gate_small34_%s.json' % label], timeout=250)
    got = [l.strip() for l in so.splitlines()
           if '"units_success"' in l or '"success"' in l]
    print('[small34] rc=%d %s' % (rc, ' '.join(got) if got else
                                  'NO SUMMARY LINE（本项未被测量，不得当作通过）: '
                                  + (se.strip().splitlines()[-1] if se.strip() else '')))
    rc, so, se = run([sys.executable, '-X', 'utf8', 'scripts/pyc_verify.py', 'selfcheck',
                      'site-packages/fly/data/quotation.pyc'], timeout=200)
    print('[selfcheck] rc=%d %s' % (rc, ' | '.join(l for l in so.splitlines() if 'selfcheck' in l)))
    rc, so, se = run([sys.executable, '-X', 'utf8', '-m', 'pytest', '-q', '--no-header',
                      '-p', 'no:cacheprovider',
                      'tests/test_algorithm_correctness.py', 'tests/test_deep_nesting_pressure.py',
                      'tests/test_control_flow_completeness_matrix.py',
                      'tests/test_complete_syntax_coverage.py', 'tests/test_boundary_cases.py',
                      'tests/test_core_functional.py'], timeout=200)
    tail = [l for l in (so + se).splitlines() if ' passed' in l or ' failed' in l]
    print('[pytest] rc=%d %s' % (rc, tail[-1] if tail else 'NO SUMMARY LINE'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('label')
    ap.add_argument('before')
    ap.add_argument('--stage', required=True, choices=('regen', 'verify', 'report', 'checks'))
    a = ap.parse_args()
    {'regen': lambda: stage_regen(a.label),
     'verify': lambda: stage_verify(a.label),
     'report': lambda: stage_report(a.label, a.before),
     'checks': lambda: stage_checks(a.label)}[a.stage]()


if __name__ == '__main__':
    main()
