# Fresh HEAD decompile + new-ruler judge for the G2b (402) and G2c (46) spaces.
# Uses the official producer (semantic_runner) so C1-C5 bind the current judge.
import json
import os
import subprocess
import sys

REPO = 'F:/Downloads/pythoncdc-main'
PY = 'D:/Python/python.exe'
WORK = 'D:/temp/opencode/cl_layout/gap/g3gap'

SPACES = [
    ('g2c', REPO + '/.trae/specs/attack-completeness-claims/rounds/round9/g2c_46/space_46.json',
     WORK + '/products_46_fresh', WORK + '/hdr_g2c'),
    ('g2b', REPO + '/.trae/specs/attack-completeness-claims/rounds/round9/g2b_402/space_402.json',
     WORK + '/products_402_fresh', WORK + '/hdr_g2b'),
]


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else 'both'
    for tag, space, products, out in SPACES:
        if which not in ('both', tag):
            continue
        cmd = [PY, '-X', 'utf8', REPO + '/tools/completeness/semantic_runner.py',
               '--space', space, '--product-dir', products, '--out', out + '.json',
               '--judge', REPO + '/tools/completeness/semantic_diff.py',
               '--timeout', '60']
        print('[run]', tag, flush=True)
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True,
                              encoding='utf-8', errors='replace')
        tail = [line for line in (proc.stdout or '').splitlines() if line.startswith('[semantic_runner]')]
        print('\n'.join(tail[-4:]), flush=True)
        print('rc=%s stderr=%s' % (proc.returncode, (proc.stderr or '')[-300:]), flush=True)
        if os.path.isfile(out + '.json'):
            data = json.load(open(out + '.json', encoding='utf-8'))
            print('[run]', tag, 'summary', json.dumps(data.get('summary'), ensure_ascii=False),
                  flush=True)


if __name__ == '__main__':
    main()
