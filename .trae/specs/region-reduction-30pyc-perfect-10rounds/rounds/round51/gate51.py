import json
import subprocess
import sys

H = 'D:/Temp/r51b/r51b.py'
R = 'D:/Temp/r51b/'


def run_list(arm, lst, out):
    cmd = [sys.executable, '-X', 'utf8', H, 'run', '--arm=' + arm, '--list=' + lst, '--out=' + out]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        print('RUN FAILED', arm, lst, (p.stderr or '')[-400:])
        return None
    return out


def tally(a, b, label):
    def load(p):
        d = {}
        with open(p, encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    d[r['path'].replace('\\', '/')] = r
        return d
    A, B = load(a), load(b)
    same = imp = reg = moved = unpaired = 0
    changed = []
    for k, ra in A.items():
        rb = B.get(k)
        if rb is None:
            unpaired += 1
            continue
        if ra['sha'] == rb['sha']:
            same += 1
            continue
        moved += 1
        if rb['matched_functions'] > ra['matched_functions']:
            imp += 1
        elif rb['matched_functions'] < ra['matched_functions']:
            reg += 1
        changed.append((k, ra['matched_functions'], ra['total_functions'], rb['matched_functions'], rb['total_functions']))
    fa = sum(1 for r in A.values() if r['matched_functions'] == r['total_functions'])
    fb = sum(1 for r in B.values() if r['matched_functions'] == r['total_functions'])
    sa = sum(r['matched_functions'] for r in A.values())
    sb = sum(r['matched_functions'] for r in B.values())
    print('%s: SAME=%d IMPROVED=%d REGRESSION=%d MOVED=%d unpaired=%d | files fully matched a=%d b=%d | sum matched a=%d b=%d'
          % (label, same, imp, reg, moved, unpaired, fa, fb, sa, sb))
    for k, ma, ta, mb, tb in changed:
        print('    %-58s %d/%d -> %d/%d' % (k.split('site-packages/')[-1][-58:], ma, ta, mb, tb))
    return [k for k, _, _, _, _ in changed]


if __name__ == '__main__':
    arm = sys.argv[1]
    which = sys.argv[2] if len(sys.argv) > 2 else 'g123'
    out = {}
    if which in ('g1', 'g123'):
        b = run_list(arm, R + 'g1_files.txt', R + 'g1_' + arm + '.jsonl')
        if b:
            out['G1'] = tally(R + 'g1_head.jsonl', b, 'G1 (17 deficit<=2 files)')
    if which in ('g2', 'g123'):
        b = run_list(arm, R + 'bat43.txt', R + 'bat43_' + arm + '.jsonl')
        if b:
            out['G2p'] = tally(R + 'bat43_head.jsonl', b, 'G2-prime (143 battery files)')
    if which in ('g3', 'g123'):
        b = run_list(arm, R + 'anchors109.txt', R + 'anch43_' + arm + '.jsonl')
        if b:
            out['G3'] = tally(R + 'anch43_head.jsonl', b, 'G3 (load-bearing anchors)')
    print('DONE', list(out))
