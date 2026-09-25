# -*- coding: utf-8 -*-
"""Round 63 close-out helpers (read-only w.r.t. the repository).

  python -X utf8 closeout63.py battery <arm> [arm2 ...]
      Run every R63 batch repro (test_repros/round63_b*/*.pyc) PLUS the six pinned R62 dd
      witnesses over each arm, printing a per-repro comparison table. This is a COMPARISON
      gate: the landed column is the baseline, the candidate column must not worsen any
      witness and must move the witness its own spec names.
  python -X utf8 closeout63.py landproof <mirr_x>
      Hash every core file of a mirror against the worktree, proving the batteries ran on
      the bytes that are actually landed.

Products are written only under D:/Temp/opencode/r67gate/build_<arm>; no site-packages
product and no pyc_index.json entry is touched.
"""
import glob
import hashlib
import io
import json
import os
import subprocess
import sys

REPO = r'F:/Downloads/pythoncdc-main'
GATE = r'D:/Temp/opencode/r67gate/fix2'
sys.stdout.reconfigure(encoding='utf-8')

PINNED = [l.strip() for l in io.open(GATE + '/shapes_r63.txt', encoding='utf-8') if l.strip()]


def repro_list():
    out = []
    dirs = sorted(glob.glob(os.path.join(REPO, 'test_repros', 'round63_b*')))
    dirs += sorted(glob.glob(os.path.join(REPO, 'test_repros', 'round63_fix*')))
    dirs += sorted(glob.glob(os.path.join(REPO, 'test_repros', 'round64_*')))
    dirs += sorted(glob.glob(os.path.join(REPO, 'test_repros', 'round65_*')))
    dirs += sorted(glob.glob(os.path.join(REPO, 'test_repros', 'round66_*')))
    dirs += sorted(glob.glob(os.path.join(REPO, 'test_repros', 'round67_*')))
    for d in dirs:
        for p in sorted(glob.glob(os.path.join(d, '*.pyc'))):
            if 'OK' in os.path.basename(p):
                continue
            out.append(p.replace('\\', '/'))
    for p in PINNED:
        if os.path.isfile(p.replace('/', os.sep)) and p not in out:
            out.append(p)
    return out


def run_arm(arm, listfile, out):
    cmd = [sys.executable, '-X', 'utf8', os.path.join(GATE, 'h62.py'), 'run',
           '--arm=%s' % arm, '--list=%s' % listfile, '--out=%s' % out, '--budget=280']
    return subprocess.run(cmd, cwd=GATE, capture_output=True, text=True, timeout=295,
                          errors='replace')


def battery(arms):
    paths = repro_list()
    print('repro pycs discovered: %d  (round63 batches + %d pinned R62 witnesses)'
          % (len(paths), len(PINNED)))
    assert paths, 'no repros yet'
    lf = GATE + '/dump/reprolist65.txt'
    io.open(lf, 'w', encoding='utf-8', newline='\n').write('\n'.join(paths) + '\n')
    res = {}
    for arm in arms:
        out = '%s/dump/repro65_%s.jsonl' % (GATE, arm)
        if os.path.isfile(out):
            os.remove(out)
        run_arm(arm, lf, out)
        rows = {}
        for l in io.open(out, encoding='utf-8'):
            if l.strip():
                r = json.loads(l)
                rows[r['path'].replace('\\', '/')] = r
        res[arm] = rows
    print('%-62s %s' % ('repro', '  '.join('%-22s' % a for a in arms)))
    worst = 0
    for p in paths:
        cells = []
        for arm in arms:
            r = res[arm].get(p)
            if r is None:
                cells.append('%-22s' % 'NO-RECORD')
            elif r.get('error'):
                cells.append('%-22s' % ('ERR ' + r['error'][:16]))
            else:
                bad = len(r['mism'] or [])
                delta = sum((m[2] or 0) - (m[1] or 0) for m in (r['mism'] or []))
                cells.append('%-22s' % ('%d/%d bad=%d d=%+d'
                                        % (r['matched_functions'], r['total_functions'], bad, delta)))
                if arm != arms[0] and (r['matched_functions'] < (res[arms[0]].get(p) or {}).get('matched_functions', 0)):
                    worst += 1
        key = p.replace('\\', '/')
        label = key.split('test_repros/')[-1] if 'test_repros/' in key else os.path.basename(key)
        print('%-62s %s' % (label, '  '.join(cells)))
    print('candidate columns worse-than-landed on %d repro(s)' % worst)
    return 0


def landproof(mirror_rel):
    mdir = os.path.join(GATE, mirror_rel)
    n = same = diff = 0
    for root, dirs, files in os.walk(os.path.join(mdir, 'core')):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in files:
            mp = os.path.join(root, f)
            rel = os.path.relpath(mp, mdir).replace('\\', '/')
            rp = os.path.join(REPO, rel.replace('/', os.sep))
            n += 1
            a = hashlib.sha256(io.open(mp, 'rb').read()).hexdigest()
            b = hashlib.sha256(io.open(rp, 'rb').read()).hexdigest() if os.path.isfile(rp) else '-'
            if a == b:
                same += 1
            else:
                diff += 1
                print('  DIFF %s  mirror=%s repo=%s' % (rel, a[:12], b[:12]))
    print('mirror %s: %d core files, same=%d diff=%d' % (mirror_rel, n, same, diff))
    return 0 if diff == 0 and n >= 20 else 1


if __name__ == '__main__':
    what = sys.argv[1]
    if what == 'battery':
        sys.exit(battery(sys.argv[2:] or ['landed']))
    elif what == 'landproof':
        sys.exit(landproof(sys.argv[2]))
    print('usage: closeout63.py battery <arm>... | closeout63.py landproof <mirr_x>')
