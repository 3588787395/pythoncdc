# Minimal driver: rerun the round9 G3 30-case sample through the new ruler.
#   python -I -X utf8 _g3_run30.py [--keep-identity] [--equivalents FILE] [--tag NAME]
import argparse
import json
import os
import subprocess
import sys
import time

REPO = 'F:/Downloads/pythoncdc-main'
PY = 'D:/Python/python.exe'
CASES_DIR = REPO + '/.trae/specs/attack-completeness-claims/rounds/round9/g3_mutation'
WORK = 'D:/temp/opencode/cl_layout/gap/g3gap'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--keep-identity', action='store_true')
    ap.add_argument('--equivalents')
    ap.add_argument('--tag', default='mut')
    ap.add_argument('--only', default='')
    args = ap.parse_args()
    outdir = os.path.join(WORK, args.tag)
    os.makedirs(outdir, exist_ok=True)
    files = sorted(f for f in os.listdir(CASES_DIR)
                   if f.startswith('case_') and f.endswith('.json'))
    if args.only:
        wanted = set(args.only.split(','))
        files = [f for f in files if any(w in f for w in wanted)]
    rows = []
    started = time.time()
    for name in files:
        case_path = os.path.join(CASES_DIR, name)
        with open(case_path, encoding='utf-8-sig') as fh:
            case = json.load(fh)
        eid = case['case_id'].replace('MUT-', '')
        source = case['product']['source']
        out = os.path.join(outdir, 'mut_%s.json' % eid)
        cmd = [PY, '-I', '-X', 'utf8', REPO + '/tools/completeness/mutation_test.py',
               '--case', case_path, '--source', source, '--max-mutants', '25', '--out', out]
        if args.keep_identity:
            cmd.append('--keep-identity')
        if args.equivalents:
            cmd.extend(['--equivalents', args.equivalents])
        t0 = time.time()
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True,
                              encoding='utf-8', errors='replace')
        report = {}
        if os.path.isfile(out):
            with open(out, encoding='utf-8') as fh:
                report = json.load(fh)
        summary = report.get('summary', {})
        rows.append({'entry_id': eid, 'rc': proc.returncode,
                     'status': report.get('status'), 'generated': report.get('generated'),
                     'selected': report.get('selected'), 'summary': summary,
                     'generator_fixes': report.get('generator_fixes', []),
                     'seconds': round(time.time() - t0, 1),
                     'stderr': (proc.stderr or '')[-400:]})
        print('%-24s rc=%d gen=%s sel=%s K=%s M=%s E=%s F=%s ERR=%s skip=%s %.0fs' % (
            eid, proc.returncode, report.get('generated'), report.get('selected'),
            summary.get('KILLED'), summary.get('MISSED'), summary.get('EQUIVALENT'),
            summary.get('FALSE_KILL'), summary.get('ERROR'), summary.get('identity_skipped'),
            time.time() - t0), flush=True)
    agg = {}
    for row in rows:
        for key in ('KILLED', 'MISSED', 'EQUIVALENT', 'FALSE_KILL', 'INCONCLUSIVE', 'ERROR',
                    'evaluated', 'identity_skipped', 'selected'):
            agg[key] = agg.get(key, 0) + int(row['summary'].get(key) or 0)
    payload = {'tag': args.tag, 'keep_identity': args.keep_identity,
               'equivalents': args.equivalents, 'cases': len(rows),
               'aggregate': agg, 'elapsed_s': round(time.time() - started, 1),
               'rows': rows}
    with open(os.path.join(WORK, 'run30_%s.json' % args.tag), 'w', encoding='utf-8',
              newline='\n') as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    print('AGG', json.dumps(agg, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
