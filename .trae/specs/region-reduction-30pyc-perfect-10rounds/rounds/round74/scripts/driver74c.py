# -*- coding: utf-8 -*-
"""Sequential driver: absj3 official 402 -> ADR absj3."""
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
C = os.path.dirname(os.path.abspath(__file__))
LIST = os.path.join(C, 'all402.txt')
LOG = os.path.join(C, 'dump', '_driver74c.log')


def io_open(p, m):
    return open(p, m, encoding='utf-8', errors='replace')


def run(args):
    p = subprocess.run([sys.executable, '-W', 'ignore', '-X', 'utf8'] + args,
                       cwd=C, capture_output=True, text=True, encoding='utf-8',
                       errors='replace')
    out = (p.stdout or '')[-1200:] + (p.stderr or '')[-800:]
    with io_open(LOG, 'a') as f:
        f.write('CMD %s -> rc=%d\n%s\n' % (' '.join(args), p.returncode, out))
    return p.returncode


def main():
    with io_open(LOG, 'w') as f:
        f.write('driver74c start\n')
    for s in range(8):
        if os.path.isfile(os.path.join(C, 'dump', 'off_absj3_s%d.jsonl' % s)) and s > 0:
            continue
        rc = run(['h62.py', 'run', '--arm=absj3', '--list=%s' % LIST,
                  '--out=dump/off_absj3_s%d.jsonl' % s, '--nshard=8', '--shard=%d' % s])
        if rc != 0:
            return 1
    rows = []
    for s in range(8):
        for line in io_open(os.path.join(C, 'dump', 'off_absj3_s%d.jsonl' % s), 'r'):
            line = line.strip()
            if line:
                rows.append(line)
    with io_open(os.path.join(C, 'dump', 'off_absj3_402.jsonl'), 'w') as f:
        f.write('\n'.join(rows) + '\n')
    rc = run(['adr73.py', 'absj3', 'fam74_r74.json'])
    with io_open(LOG, 'a') as f:
        f.write('driver74c done rc=%d\n' % rc)
    return rc


if __name__ == '__main__':
    sys.exit(main())
